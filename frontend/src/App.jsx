import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Tere! Olen sinu nutikas dokumentide assistent. Kuidas saan aidata?', sources: [] }]);
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${API_URL}/documents/`);
      setDocuments(res.data.documents || []);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    try {
      await axios.post(`${API_URL}/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchDocuments();
      
      // Notify via chat quietly
      setMessages(prev => [...prev, { role: 'bot', text: `Fail "${file.name}" edukalt lisatud!` }]);
    } catch (err) {
      console.error('Upload failed', err);
      alert('Faili üleslaadimine ebaõnnestus.');
    } finally {
      setIsUploading(false);
      e.target.value = null; // reset
    }
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Kas soovid kustutada dokumenti: ${filename}?`)) return;
    
    try {
      await axios.delete(`${API_URL}/documents/${filename}`);
      fetchDocuments();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userQuery = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
    setIsTyping(true);

    try {
      const res = await axios.post(`${API_URL}/ask/`, { query: userQuery });
      const { answer, sources } = res.data;
      
      setMessages(prev => [...prev, { role: 'bot', text: answer, sources }]);
    } catch (err) {
      console.error('Query failed:', err);
      setMessages(prev => [...prev, { role: 'bot', text: 'Vabandust, tekkis süsteemiviga päringu töötlemisel.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app-container">
      
      {/* Sidebar: Document Management */}
      <aside className="sidebar glass-panel">
        <div className="sidebar-header">
          <h2>Tark Otsing</h2>
          <p>Dokumentide intelligentne otsingusüsteem</p>
        </div>

        <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
          {isUploading ? (
            <div className="loader-spinner" style={{borderColor: "rgba(255,255,255,0.1)", borderTopColor: "var(--primary)", width: "32px", height: "32px"}} />
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          )}
          <p>{isUploading ? 'Laadimine...' : 'Klõpsa faili valimiseks'}</p>
          <span className="types">Toetatud failid: .pdf, .docx, .txt</span>
        </div>
        <input 
          type="file" 
          ref={fileInputRef} 
          className="file-input" 
          accept=".pdf,.docx,.txt"
          onChange={handleFileUpload} 
        />

        <div className="document-list">
          {documents.map((doc, idx) => (
             <div className="document-item" key={idx}>
               <span className="document-name" title={doc}>{doc}</span>
               <button className="btn-delete" onClick={() => handleDelete(doc)}>
                 <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                   <polyline points="3 6 5 6 21 6"></polyline>
                   <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                 </svg>
               </button>
             </div>
          ))}
          {documents.length === 0 && (
            <p style={{textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-placeholder)', marginTop: '20px'}}>
              Pole veel üles laaditud dokumente.
            </p>
          )}
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="chat-container glass-panel">
        <div className="chat-header">
          <h3>Vestlus</h3>
        </div>

        <div className="chat-messages">
          {messages.map((msg, index) => (
             <div className={`message ${msg.role}`} key={index}>
               <div className={`avatar ${msg.role}`}>
                 {msg.role === 'user' ? 'M' : 'AI'}
               </div>
               <div style={{display: 'flex', flexDirection: 'column'}}>
                 <div className="message-bubble">
                   {msg.text}
                 </div>
                 {msg.sources && msg.sources.length > 0 && (
                   <div className="sources-pill">
                     {msg.sources.map((src, i) => (
                       <span className="source-tag" key={i}>📄 {src}</span>
                     ))}
                   </div>
                 )}
               </div>
             </div>
          ))}
          {isTyping && (
             <div className="message bot">
                <div className="avatar bot">AI</div>
                <div className="message-bubble" style={{display: 'flex', gap: '4px', alignItems: 'center'}}>
                   <span className="loader-spinner" style={{width: '12px', height: '12px', borderTopColor: 'var(--text-secondary)'}}></span> 
                   <span style={{fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '8px'}}>Otsib ja kirjutab...</span>
                </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <div className="input-box">
            <textarea 
              placeholder="Küsi midagi oma dokumentide kohta..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isTyping}
            />
            <button className="btn-send" onClick={sendMessage} disabled={isTyping || !inputValue.trim()}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </main>

    </div>
  );
}

export default App;
