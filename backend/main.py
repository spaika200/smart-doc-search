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

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search API! The server is running."}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Use our new document loader that handles PDF, DOCX, and TXT
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


@app.post("/ask/")
async def ask_question(request: QueryRequest):
    """
    RAG Endpoint: takes a query, runs nearest-neighbor search, and gets an answer from LLM.
    """
    try:
        response = generate_rag_response(request.query)
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