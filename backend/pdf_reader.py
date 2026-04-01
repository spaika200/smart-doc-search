from pypdf import PdfReader
import os

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        return f"Error: The file '{pdf_path}' was not found in the backend folder."

    print(f"Opening '{pdf_path}'...")
    reader = PdfReader(pdf_path)
    extracted_text = ""
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
        print(f"Processed page {i + 1}/{len(reader.pages)}")
            
    return extracted_text

if __name__ == "__main__":
    file_name = "test.pdf"
    
    result = extract_text_from_pdf(file_name)
    
    print("\n--- EXTRACTED TEXT (First 500 characters) ---")
    print(result[:500]) 
    print("---------------------------------------------")