from fastapi import FastAPI, UploadFile, File
import shutil
import os
from pdf_reader import extract_text_from_pdf
from text_processor import split_text_into_chunks # <-- NEW IMPORT
from embedder import process_and_save_chunks

app = FastAPI(title="Smart Document Search API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search API! The server is running."}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(temp_file_path)
    
    text_chunks = split_text_into_chunks(extracted_text)
    
    # Generate embeddings and save to database
    process_and_save_chunks(file.filename, text_chunks)
    
    os.remove(temp_file_path)
    
    return {
        "filename": file.filename, 
        "total_chunks": len(text_chunks),
        "first_chunk_preview": text_chunks[0] if text_chunks else "No text found."
    }