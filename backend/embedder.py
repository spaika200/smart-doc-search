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
        
    # Initialize the embedding model
    embedder = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Generate vector embeddings
    embeddings = embedder.embed_documents(text_chunks)
    
    # Connect to PostgreSQL and insert the records
    conn = get_db_connection()
    try:
        # Register the vector extension to handle VECTOR type in PostgreSQL
        register_vector(conn)
        
        cur = conn.cursor()
        
        # Insert each chunk with its embedding
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
