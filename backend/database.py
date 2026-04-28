import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Returns a connection to the PostgreSQL database."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "smart_search"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

def init_db():
    """Initializes the database by creating the pgvector extension and the necessary tables."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Enable the vector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create the document_chunks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id SERIAL PRIMARY KEY,
                filename TEXT,
                chunk_text TEXT,
                embedding VECTOR(3072)
            );
        """)
        
        # Create chats table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id SERIAL PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create chat_messages table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
                role TEXT,
                text TEXT,
                sources TEXT,
                context_snippets TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cur.close()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
