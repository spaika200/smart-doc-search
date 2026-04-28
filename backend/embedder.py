import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pgvector.psycopg2 import register_vector
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

def process_and_save_chunks(filename: str, text_chunks: list):
    """
    Generates embeddings for a list of text chunks and saves them to the database.
    """
    if not text_chunks:
        return
        
    embedder = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    embeddings = embedder.embed_documents(text_chunks)
    
    conn = get_db_connection()
    try:
        register_vector(conn)
        
        cur = conn.cursor()
        
        for chunk, embedding in zip(text_chunks, embeddings):
            cur.execute(
                """
                INSERT INTO document_chunks (filename, chunk_text, embedding)
                VALUES (%s, %s, %s);
                """,
                (filename, chunk, embedding)
            )
            
        conn.commit()
        cur.close()
    finally:
        conn.close()
