import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Tere! Olen sinu nutikas dokumentide assistent. Kuidas saan aidata?', sources: [], context_snippets: [] }]);
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [modalSnippet, setModalSnippet] = useState(null); // {filename, text}
  const [selectedTone, setSelectedTone] = useState('Tavaline');
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);

  const SUGGESTED_CHIPS = ["Millised dokumendid on andmebaasis?", "Tee lühikokkuvõte", "Kuidas see süsteem töötab?"];
  
  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
  };
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      const res = await axios.get(`${API_URL}/chats/`);
      setChats(res.data.chats || []);
    } catch (err) {
      console.error('Error fetching chats:', err);
    }
  };

  const loadChat = async (chatId) => {
    setActiveChatId(chatId);
    try {
      const res = await axios.get(`${API_URL}/chats/${chatId}/messages`);
      if (res.data.messages && res.data.messages.length > 0) {
        setMessages(res.data.messages);
      } else {
        setMessages([{ role: 'bot', text: 'Tere! Olen sinu nutikas dokumentide assistent. Kuidas saan aidata?', sources: [], context_snippets: [] }]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const createNewChat = async () => {
    try {
      const res = await axios.post(`${API_URL}/chats/`, { title: "Uus vestlus" });
      const newChatId = res.data.id;
      setChats(prev => [res.data, ...prev]);
      setActiveChatId(newChatId);
      setMessages([{ role: 'bot', text: 'Tere! Olen sinu nutikas dokumentide assistent. Kuidas saan aidata?', sources: [], context_snippets: [] }]);
    } catch (err) {
      console.error(err);
    }
  };

  const deleteChat = async (chatId) => {
    if (!window.confirm("Kas oled kindel, et soovid selle vestluse kustutada?")) return;
    try {
      await axios.delete(`${API_URL}/chats/${chatId}`);
      setChats(prev => prev.filter(c => c.id !== chatId));
      if (activeChatId === chatId) {
        setActiveChatId(null);
        setMessages([{ role: 'bot', text: 'Tere! Olen sinu nutikas dokumentide assistent. Kuidas saan aidata?', sources: [], context_snippets: [] }]);
      }
    } catch (err) {
      console.error('Error deleting chat:', err);
    }
  };

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
      setMessages(prev => [...prev, { role: 'bot', text: `Fail **${file.name}** edukalt lisatud!` }]);
    } catch (err) {
      console.error('Upload failed', err);
      alert('Faili üleslaadimine ebaõnnestus.');
    } finally {
      setIsUploading(false);
      e.target.value = null; 
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
    
    // Package history to send (latest 6 messages, filtering out system notifications without sources if we want)
    const historyPayload = messages.map(m => ({ role: m.role, text: m.text }));
    
    setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
    setIsTyping(true);

    try {
      if (!activeChatId) {
         // Create chat if none exists
         const cRes = await axios.post(`${API_URL}/chats/`, { title: userQuery.substring(0, 30) });
         setActiveChatId(cRes.data.id);
         setChats(prev => [cRes.data, ...prev]);
         // wait for state update in a real app, but here we can just use the ID
         await streamResponse(userQuery, historyPayload, cRes.data.id);
      } else {
         await streamResponse(userQuery, historyPayload, activeChatId);
      }
    } catch (err) {
      console.error('Query failed:', err);
      setMessages(prev => [...prev, { role: 'bot', text: 'Vabandust, tekkis süsteemiviga päringu töötlemisel.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const streamResponse = async (query, history, chatId) => {
      const res = await fetch(`${API_URL}/ask/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          query: query,
          history: history,
          tone: selectedTone,
          chat_id: chatId
        })
      });

      if (!res.ok) throw new Error("Network error");
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let botText = "";
      let botSources = [];
      let botSnippets = [];
      
      setMessages(prev => [...prev, { role: 'bot', text: '', sources: [], context_snippets: [] }]);
      setIsTyping(false); // hide loader since stream started

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunkStr = decoder.decode(value, { stream: true });
        
        const lines = chunkStr.split("\n\n");
        for (const line of lines) {
           if (line.startsWith("data: ")) {
              const dataStr = line.slice(6);
              if (dataStr === "[DONE]") break;
              try {
                 const data = JSON.parse(dataStr);
                 if (data.type === "metadata") {
                    botSources = data.sources;
                    botSnippets = data.context_snippets;
                 } else if (data.type === "chunk") {
                    botText += data.text;
                 }
                 
                 setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1] = {
                       role: 'bot',
                       text: botText,
                       sources: botSources,
                       context_snippets: botSnippets
                    };
                    return newMsgs;
                 });
              } catch(e) {}
           }
        }
      }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const openSnippetModal = (filename, snippets) => {
    // Find the specific snippet text from the backend's returned array
    const snippetData = snippets?.find(s => s.filename === filename);
    if (snippetData) {
      setModalSnippet(snippetData);
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
            <div className="loader-spinner" style={{borderTopColor: "var(--primary)", width: "32px", height: "32px"}} />
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

        <div className="sidebar-tabs" style={{ display: 'flex', gap: '10px' }}>
            <button style={{ flex: 1, padding: '10px', background: 'var(--primary)', color: 'white', borderRadius: '8px', fontWeight: 500 }} onClick={createNewChat}>+ Uus Vestlus</button>
        </div>
        
        <div className="chat-history-list" style={{ maxHeight: '180px', overflowY: 'auto', borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px' }}>
          <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>Ajalugu</h4>
          {chats.map(c => (
             <div 
               key={c.id} 
               style={{ 
                 display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                 padding: '8px 12px', 
                 cursor: 'pointer', 
                 borderRadius: '6px', 
                 background: activeChatId === c.id ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                 color: activeChatId === c.id ? 'var(--primary)' : 'var(--text-secondary)',
                 fontSize: '0.9rem',
                 marginBottom: '4px',
                 transition: 'all 0.2s'
               }}
             >
               <span onClick={() => loadChat(c.id)} style={{ flex: 1 }}>💬 {c.title}</span>
               <button 
                 onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} 
                 style={{
                    background: 'transparent', border: 'none', color: 'var(--text-secondary)',
                    cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center',
                    opacity: 0.6
                 }}
                 title="Kustuta vestlus"
                 onMouseOver={(e) => e.currentTarget.style.color = 'red'}
                 onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
               >
                 <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
               </button>
             </div>
          ))}
          {chats.length === 0 && (
            <p style={{fontSize: '0.8rem', color: 'var(--text-placeholder)'}}>Pole varasemaid vestlusi.</p>
          )}
        </div>

        <div className="document-list">
          <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>Dokumendid</h4>
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
               <div style={{display: 'flex', flexDirection: 'column', width: '100%'}}>
                 <div className="message-bubble">
                   <ReactMarkdown>{msg.text}</ReactMarkdown>
                 </div>
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                   {msg.sources && msg.sources.length > 0 ? (
                     <div className="sources-pill" style={{ marginTop: 0 }}>
                       {msg.sources.map((src, i) => (
                         <span 
                           className="source-tag clickable" 
                           key={i}
                           onClick={() => openSnippetModal(src, msg.context_snippets)}
                         >
                           📄 {src}
                         </span>
                       ))}
                     </div>
                   ) : <div />}
                   {msg.role === 'bot' && (
                     <button className="btn-copy" onClick={() => handleCopy(msg.text)} title="Kopeeri vastus" style={{ marginTop: 0 }}>
                       <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                         <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                         <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                       </svg>
                       Kopeeri
                     </button>
                   )}
                 </div>
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
          {messages.length === 1 && (
            <div className="suggested-chips">
              {SUGGESTED_CHIPS.map((chip, idx) => (
                <div key={idx} className="chip" onClick={() => setInputValue(chip)}>
                  {chip}
                </div>
              ))}
            </div>
          )}
          
          <div className="tone-toggles">
            {['Tavaline', 'Lihtne keel', 'Lühikokkuvõte', 'Juriidiline'].map(tone => (
              <button 
                key={tone} 
                className={`tone-btn ${selectedTone === tone ? 'active' : ''}`}
                onClick={() => setSelectedTone(tone)}
              >
                {tone}
              </button>
            ))}
          </div>

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

      {/* Snippet Modal Overlay */}
      {modalSnippet && (
        <div className="modal-overlay" onClick={() => setModalSnippet(null)}>
          <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h4>Algallikas ({modalSnippet.filename})</h4>
              <button className="btn-close" onClick={() => setModalSnippet(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p className="snippet-text">"{modalSnippet.text}"</p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
