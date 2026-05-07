import os
import docx
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        return ""

    print(f"Opening '{pdf_path}'...")
    reader = PdfReader(pdf_path)
    extracted_text = ""
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
        print(f"Processed page {i + 1}/{len(reader.pages)}")
            
    return extracted_text

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
