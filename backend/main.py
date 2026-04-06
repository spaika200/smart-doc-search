from fastapi import FastAPI, UploadFile, File
import shutil
import os
from pdf_reader import extract_text_from_pdf

app = FastAPI(title="Smart Document Search API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Document Search API! The server is running."}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    # 1. Save the uploaded file temporarily to the server
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(temp_file_path)
    
    os.remove(temp_file_path)
    
    return {
        "filename": file.filename, 
        "message": "File processed successfully!",
        "text_preview": extracted_text[:500]
    }