from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os

from document_loader import extract_text_from_file
from text_processor import split_text_into_chunks
from embedder import process_and_save_chunks
from vector_search import generate_rag_response
from database import get_db_connection

app = FastAPI(title="Smart Document Search API")

# Setup CORS to allow React Frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import List, Optional
import json
from fastapi.responses import StreamingResponse

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []
    tone: Optional[str] = "Tavaline"
    chat_id: Optional[int] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search API! The server is running."}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text based on file format (PDF, DOCX, TXT)
    extracted_text = extract_text_from_file(temp_file_path, file.filename)
    
    if not extracted_text:
        os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail="Failed to extract text. Unsupported or empty file.")
        
    text_chunks = split_text_into_chunks(extracted_text)
    
    # Generate embeddings and save to database
    process_and_save_chunks(file.filename, text_chunks)
    
    os.remove(temp_file_path)
    
    return {
        "filename": file.filename, 
        "total_chunks": len(text_chunks),
        "message": "Fail on edukalt üles laaditud ja indekseeritud!"
    }


@app.post("/chats/")
def create_chat(request: dict):
    title = request.get("title", "Uus vestlus")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO chats (title) VALUES (%s) RETURNING id, title, created_at;", (title,))
        chat = cur.fetchone()
        conn.commit()
        return {"id": chat[0], "title": chat[1]}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

from vector_search import generate_chat_title

import time

@app.post("/chats/{chat_id}/generate_title")
def generate_and_update_title(chat_id: int, request: dict):
    query = request.get("query", "")
    if not query:
        return {"title": "Uus vestlus"}
        
    time.sleep(2) # Delay to prevent Gemini API 429 concurrent request rate limit
    title = generate_chat_title(query)
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE chats SET title = %s WHERE id = %s;", (title, chat_id))
        conn.commit()
        return {"title": title}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/chats/")
def list_chats():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM chats ORDER BY created_at DESC;")
        chats = cur.fetchall()
        return {"chats": [{"id": c[0], "title": c[1]} for c in chats]}
    finally:
        conn.close()

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM chats WHERE id = %s;", (chat_id,))
        conn.commit()
        return {"message": "Vestlus kustutatud"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/chats/{chat_id}/messages")
def get_chat_messages(chat_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT role, text, sources, context_snippets FROM chat_messages WHERE chat_id = %s ORDER BY created_at ASC;", (chat_id,))
        messages = cur.fetchall()
        result = []
        for m in messages:
            sources = json.loads(m[2]) if m[2] else []
            snippets = json.loads(m[3]) if m[3] else []
            result.append({"role": m[0], "text": m[1], "sources": sources, "context_snippets": snippets})
        return {"messages": result}
    finally:
        conn.close()

def save_message(chat_id, role, text, sources=None, snippets=None):
    if not chat_id: return
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        s_json = json.dumps(sources) if sources else None
        cs_json = json.dumps(snippets) if snippets else None
        cur.execute("INSERT INTO chat_messages (chat_id, role, text, sources, context_snippets) VALUES (%s, %s, %s, %s, %s);",
                    (chat_id, role, text, s_json, cs_json))
        conn.commit()
    finally:
        conn.close()

from vector_search import generate_rag_response

@app.post("/ask/")
async def ask_question(request: QueryRequest):
    """
    RAG Endpoint: takes a query, runs nearest-neighbor search, and gets an answer from LLM.
    """
    try:
        if request.chat_id:
            save_message(request.chat_id, "user", request.query)

        try:
            response = generate_rag_response(request.query, request.history, request.tone)
        except Exception as api_err:
            if "429" in str(api_err) or "RESOURCE_EXHAUSTED" in str(api_err):
                response = {
                    "answer": "⚠️ **Google API tasuta päringute limiit on täitunud** (20 päringut minutis). Palun oodake 60 sekundit ja proovige uuesti.",
                    "sources": [],
                    "context_snippets": []
                }
            else:
                raise api_err
        
        if request.chat_id:
            save_message(request.chat_id, "bot", response["answer"], response["sources"], response["context_snippets"])
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/")
def list_documents():
    """
    Returns a list of all distinct filenames from the database.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT filename FROM document_chunks;")
        results = cur.fetchall()
        documents = [row[0] for row in results]
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.delete("/documents/{filename}")
def delete_document(filename: str):
    """
    Deletes all vector chunks associated with the specified filename.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM document_chunks WHERE filename = %s;", (filename,))
        deleted_count = cur.rowcount
        conn.commit()
        return {"message": f"Successfully deleted '{filename}'", "deleted_chunks": deleted_count}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()