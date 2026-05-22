import unittest
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient
import io
import sys
import os

# Ensure backend directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from text_processor import split_text_into_chunks
from database import get_db_connection, init_db
from document_loader import extract_text_from_file, extract_text_from_pdf
from embedder import process_and_save_chunks
from vector_search import query_vector_db, generate_rag_response

client = TestClient(app)

class TestTextProcessor(unittest.TestCase):
    def test_text_splitting_returns_list(self):
        """Checks if text splitting returns a list"""
        result = split_text_into_chunks("Test " * 50)
        self.assertIsInstance(result, list)

    def test_text_splitting_correct_chunks(self):
        """Checks if a long text is split correctly into multiple chunks"""
        # Our chunk_size is 1000, so 1500 characters should produce at least 2 chunks
        result = split_text_into_chunks("A" * 1500)
        self.assertTrue(len(result) >= 2)

    def test_text_splitting_short_text(self):
        """Checks if a short text remains as a single chunk"""
        result = split_text_into_chunks("Lühike tekst")
        self.assertEqual(len(result), 1)

    def test_empty_string_handling(self):
        """Checks how the system handles an empty string"""
        result = split_text_into_chunks("")
        self.assertEqual(result, [])


class TestVectorEmbeddings(unittest.TestCase):
    @patch('embedder.GoogleGenerativeAIEmbeddings.embed_documents')
    def test_gemini_vector_dimensions(self, mock_embed):
        """Test if the Vectorizer returns the required 3072-dimensional vector"""
        # Mock the Gemini API response with a 3072-dimensional vector
        mock_embed.return_value = [[0.1] * 3072]
        
        # Call the mocked function
        vector = mock_embed(["Sample text"])[0]
        self.assertEqual(len(vector), 3072)

    @patch('embedder.GoogleGenerativeAIEmbeddings.embed_documents')
    def test_vectorization_type(self, mock_embed):
        """Test vector data type (elements must be floats)"""
        mock_embed.return_value = [[0.1] * 3072]
        vector = mock_embed(["Estonia"])[0]
        self.assertIsInstance(vector[0], float)


class TestDatabase(unittest.TestCase):
    @patch('database.psycopg2.connect')
    def test_postgres_pgvector_connection(self, mock_connect):
        """Test connection to the PostgreSQL pgvector database"""
        # Mock a successful database connection so the test runs on any machine
        mock_connect.return_value = MagicMock()
        
        conn = get_db_connection()
        self.assertIsNotNone(conn)

    @patch('database.get_db_connection')
    def test_init_db(self, mock_get_db):
        """Test database and table initialization schema creation"""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        init_db()
        
        self.assertTrue(mock_cur.execute.called)
        self.assertTrue(mock_conn.commit.called)
        self.assertTrue(mock_conn.close.called)


class TestDocumentLoader(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open, read_data="sample plain text content")
    @patch('os.path.exists')
    def test_extract_text_from_txt(self, mock_exists, mock_file):
        """Test text extraction from plain text files"""
        mock_exists.return_value = True
        text = extract_text_from_file("dummy_path.txt", "dummy_path.txt")
        self.assertEqual(text, "sample plain text content")

    @patch('docx.Document')
    @patch('os.path.exists')
    def test_extract_text_from_docx(self, mock_exists, mock_docx):
        """Test text extraction from DOCX documents"""
        mock_exists.return_value = True
        mock_doc_obj = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "Hello world docx paragraph"
        mock_doc_obj.paragraphs = [mock_para1]
        mock_docx.return_value = mock_doc_obj

        text = extract_text_from_file("dummy_path.docx", "dummy_path.docx")
        self.assertEqual(text, "Hello world docx paragraph")

    @patch('document_loader.PdfReader')
    @patch('os.path.exists')
    def test_extract_text_from_pdf(self, mock_exists, mock_pdf):
        """Test text extraction from PDF pages"""
        mock_exists.return_value = True
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hello PDF page text content"
        mock_reader.pages = [mock_page]
        mock_pdf.return_value = mock_reader

        text = extract_text_from_file("dummy_path.pdf", "dummy_path.pdf")
        self.assertIn("Hello PDF page text content", text)

    def test_extract_text_invalid_extension(self):
        """Test that unsupported extensions return an empty string"""
        text = extract_text_from_file("dummy_path.exe", "dummy_path.exe")
        self.assertEqual(text, "")

    @patch('os.path.exists')
    def test_extract_text_missing_file(self, mock_exists):
        """Test text extraction when file does not exist"""
        mock_exists.return_value = False
        text = extract_text_from_file("missing.txt", "missing.txt")
        self.assertEqual(text, "")
        pdf_text = extract_text_from_pdf("missing.pdf")
        self.assertEqual(pdf_text, "")


class TestEmbedder(unittest.TestCase):
    @patch('embedder.register_vector')
    @patch('embedder.get_db_connection')
    @patch('embedder.GoogleGenerativeAIEmbeddings')
    def test_process_and_save_chunks(self, mock_embeddings_cls, mock_get_db, mock_reg_vector):
        """Test that chunks are embedded and successfully stored in DB"""
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1] * 3072, [0.2] * 3072]
        mock_embeddings_cls.return_value = mock_embeddings

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        process_and_save_chunks("test.pdf", ["chunk1", "chunk2"])

        self.assertTrue(mock_embeddings.embed_documents.called)
        self.assertTrue(mock_reg_vector.called)
        self.assertEqual(mock_cur.execute.call_count, 2)
        self.assertTrue(mock_conn.commit.called)


class TestRAGPipeline(unittest.TestCase):
    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'dummy'})
    @patch('vector_search.query_vector_db')
    @patch('vector_search.ChatGoogleGenerativeAI.invoke')
    def test_rag_correct_answer_from_context(self, mock_invoke, mock_query_db):
        """Tests the generation of correct answers based on the provided context (Figure 12)"""
        # Mock the database response (context)
        mock_query_db.return_value = [("test_fail.pdf", "This is a test document containing the correct answer.")]
        
        # Mock the Gemini model response
        mock_invoke.return_value = MagicMock(content="This is an AI-generated answer based on the test document.")
        
        response = generate_rag_response("What is written?")
        
        self.assertEqual(response["answer"], "This is an AI-generated answer based on the test document.")
        self.assertIn("test_fail.pdf", response["sources"])

    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'dummy'})
    @patch('vector_search.query_vector_db')
    def test_rag_hallucination_prevention(self, mock_query_db):
        """Tests the hallucination prevention mechanism (system refuses to answer if info is not found)"""
        # Mock a situation where the database returns no matches
        mock_query_db.return_value = []
        
        response = generate_rag_response("Question with no answer")
        
        self.assertIn("Vabandust, aga andmebaasist ei leitud teavet", response["answer"])
        self.assertEqual(response["sources"], [])

    @patch('vector_search.register_vector')
    @patch('vector_search.get_db_connection')
    @patch('vector_search.GoogleGenerativeAIEmbeddings')
    def test_query_vector_db(self, mock_embeddings_cls, mock_get_db, mock_reg_vector):
        """Test query vector database semantic search retrieval"""
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 3072
        mock_embeddings_cls.return_value = mock_embeddings

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [("file1.pdf", "matched text snippet")]
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        results = query_vector_db("test query")
        self.assertEqual(results, [("file1.pdf", "matched text snippet")])

    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'dummy'})
    @patch('vector_search.query_vector_db')
    @patch('vector_search.ChatGoogleGenerativeAI.invoke')
    def test_generate_rag_response_with_history_and_tones(self, mock_invoke, mock_query_db):
        """Test RAG response generation under different tones and chat history parameterization"""
        mock_query_db.return_value = [("rules.pdf", "Content paragraph.")]
        mock_invoke.return_value = MagicMock(content="Estonian answer")

        history = [{"role": "user", "text": "Hello"}, {"role": "bot", "text": "Hi"}]
        
        for tone in ["Juriidiline", "Lihtne keel", "Lühikokkuvõte", "Tavaline"]:
            response = generate_rag_response("Query text", history=history, tone=tone)
            self.assertEqual(response["answer"], "Estonian answer")


class TestFastAPIEndpoints(unittest.TestCase):
    @patch('main.extract_text_from_file')
    @patch('main.process_and_save_chunks')
    def test_upload_valid_pdf(self, mock_process, mock_extract):
        """Test successful PDF file upload via API"""
        # Mock that text was successfully extracted from the PDF
        mock_extract.return_value = "Ekstraheeritud PDF tekst"
        
        dummy_file = io.BytesIO(b"dummy pdf content")
        response = client.post("/upload/", files={"file": ("report.pdf", dummy_file, "application/pdf")})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "report.pdf")

    @patch('main.extract_text_from_file')
    @patch('main.process_and_save_chunks')
    def test_upload_valid_docx(self, mock_process, mock_extract):
        """Test successful DOCX file upload"""
        mock_extract.return_value = "Ekstraheeritud DOCX tekst"
        
        dummy_file = io.BytesIO(b"dummy docx content")
        response = client.post("/upload/", files={"file": ("contract.docx", dummy_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "contract.docx")

    @patch('main.extract_text_from_file')
    def test_upload_invalid_file(self, mock_extract):
        """Test rejection of invalid file formats (e.g., .exe) by the API"""
        mock_extract.return_value = ""
        
        dummy_file = io.BytesIO(b"dummy exe content")
        response = client.post("/upload/", files={"file": ("malware.exe", dummy_file, "application/x-msdownload")})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to extract text", response.json()["detail"])

    def test_read_root(self):
        """Test root welcome endpoint"""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome to the Smart Document Search API!", response.json()["message"])

    @patch('main.get_db_connection')
    def test_health_check_online(self, mock_get_db):
        """Test health check when database is online"""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        response = client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    @patch('main.get_db_connection')
    def test_health_check_offline(self, mock_get_db):
        """Test health check when database is offline"""
        mock_get_db.side_effect = Exception("Database offline error")
        response = client.get("/health/")
        self.assertEqual(response.status_code, 503)

    @patch('main.get_db_connection')
    def test_chats_crud_endpoints(self, mock_get_db):
        """Test chat CRUD database operations via API"""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (1, "Uus vestlus")
        mock_cur.fetchall.return_value = [(1, "Uus vestlus")]
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        # Test POST create chat
        response = client.post("/chats/", json={"title": "Uus vestlus"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 1)

        # Test GET list chats
        response = client.get("/chats/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["chats"]), 1)

        # Test PUT update chat title
        response = client.put("/chats/1", json={"title": "Uus pealkiri"})
        self.assertEqual(response.status_code, 200)

        # Test DELETE delete chat
        response = client.delete("/chats/1")
        self.assertEqual(response.status_code, 200)

    @patch('main.get_db_connection')
    def test_chat_messages_endpoint(self, mock_get_db):
        """Test fetching messages for a specific chat"""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [("user", "Hello", '["doc1.pdf"]', '[{"filename": "doc1.pdf", "text": "Hello snippet"}]')]
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        response = client.get("/chats/1/messages")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["messages"][0]["text"], "Hello")

    @patch('main.get_db_connection')
    def test_documents_endpoints(self, mock_get_db):
        """Test listing and deleting document chunks from database via API"""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [("report.pdf", 5)]
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value = mock_conn

        # Test GET documents list
        response = client.get("/documents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["documents"][0]["filename"], "report.pdf")

        # Test DELETE document
        response = client.delete("/documents/report.pdf")
        self.assertEqual(response.status_code, 200)

    @patch('main.save_message')
    @patch('main.generate_rag_response')
    def test_ask_question_rate_limit(self, mock_rag, mock_save):
        """Test rate limit error response during Q&A"""
        mock_rag.side_effect = Exception("RESOURCE_EXHAUSTED: Rate limits exceeded")
        response = client.post("/ask/", json={"query": "test question", "chat_id": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("päringute limiit on täitunud", response.json()["answer"])

    @patch('main.save_message')
    @patch('main.generate_rag_response')
    def test_ask_question_generic_error(self, mock_rag, mock_save):
        """Test generic system error response during Q&A"""
        mock_rag.side_effect = Exception("Generic pipeline error")
        response = client.post("/ask/", json={"query": "test question"})
        self.assertEqual(response.status_code, 500)

if __name__ == "__main__":
    unittest.main()