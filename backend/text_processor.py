from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text_into_chunks(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200, 
        length_function=len
    )
    
    chunks = text_splitter.split_text(text)
    return chunks

if __name__ == "__main__":
    sample_text = "See on väga pikk tekst. " * 100
    chunks = split_text_into_chunks(sample_text)
    print(f"Split text into {len(chunks)} chunks!")