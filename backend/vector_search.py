from database import get_db_connection
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

def query_vector_db(query: str, top_k: int = 4):
    """Embeds the query and retrieves the most similar chunks from PostgreSQL using pgvector."""
    # Ensure using the exact same embedding model used during document ingestion
    embedder = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    try:
        query_vector = embedder.embed_query(query)
    except Exception as e:
        print(f"Error calling embed_query: {e}")
        return []
    
    conn = get_db_connection()
    try:
        register_vector(conn)
        cur = conn.cursor()
        
        # pgvector cosine distance operator is <=>
        cur.execute(
            """
            SELECT filename, chunk_text
            FROM document_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_vector, top_k)
        )
        results = cur.fetchall()
        cur.close()
        return results
    finally:
        conn.close()

def generate_rag_response(query: str, history: list = None):
    """
    RAG Pipeline:
    1. Grabs top context from vector database
    2. Constructs prompt
    3. Triggers Gemini to answer strictly based on context & in Estonian
    """
    results = query_vector_db(query)
    if not results:
        return {
            "answer": "Vabandust, aga andmebaasist ei leitud teavet teie küsimusele vastamiseks.",
            "sources": [],
            "context_snippets": []
        }
    
    # 2. Format Context
    context_text = ""
    sources = set()
    for filename, chunk in results:
        context_text += f"\n--- [Allikas: {filename}] ---\n{chunk}\n"
        sources.add(filename)
        
    # 3. Compile history mapping
    history_str = ""
    if history:
        # Get last 5 messages to avoid blowing up context window
        recent_history = history[-5:]
        history_str = "KONTEKSTI AJALUGU (EELNEV VESTLUS):\n"
        for msg in recent_history:
            role_label = "Kasutaja" if msg.get("role") == "user" else "Sina (AI)"
            history_str += f"{role_label}: {msg.get('text')}\n"
            
    # 4. Setup Prompt to force strict adherence to context and respond in Estonian
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    prompt = f"""
    You are an intelligent document search assistant (Nutikas dokumentide otsingusüsteem).
    Your task is to answer the user's question based strictly on the provided Context. 
    Do NOT invent facts, hallucinate, or rely on external knowledge.
    If the answer cannot be confidently deduced from the Context, tell the user politely (in Estonian) that the document does not contain this information.
    You MUST answer in Estonian language.

    {history_str}

    Context:
    {context_text}
    
    USER QUESTION: {query}
    
    Vastus:
    """
    
    llm_response = llm.invoke(prompt)
    
    return {
        "answer": llm_response.content,
        "sources": list(sources),
        "context_snippets": [{"filename": r[0], "text": r[1]} for r in results]
    }
