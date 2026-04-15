import os
import docx
from pdf_reader import extract_text_from_pdf

def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Extracts text based on the uploaded file format.
    Supports .pdf, .docx, and .txt.
    """
    if not os.path.exists(file_path):
        return ""
        
    ext = filename.lower().split('.')[-1]
    
    try:
        if ext == 'pdf':
            return extract_text_from_pdf(file_path)
        elif ext == 'docx':
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif ext == 'txt':
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return ""
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ""
