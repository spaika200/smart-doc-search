# Dokumentide Intelligentne Otsingusüsteem (Smart Document Search)

Idee ja Lõputöö: Artjom Aristov & Nikita Žuravljov

This is a Full-stack Retrieval-Augmented Generation (RAG) system built to parse physical documents into vector embeddings and reliably answer queries strictly using the provided documents.

---

## 🚀 Tech Stack & AI Models

### AI Architecture (Powered by Google Gemini)
* **Embedding Model:** `models/gemini-embedding-001` 
  * Converts the `.pdf`, `.docx`, and `.txt` contents into mathematical vectors (3072 dimensions used).
* **Generation Model (LLM):** `models/gemini-2.5-flash`
  * This is the brain answering the questions. It reads the top-matched vector snippets from the database and constructs the final Estonian response without hallucinating outside knowledge.

### Frameworks Setup
* **Backend:** `FastAPI` (Python)
* **Frontend:** `React` with `Vite` (JavaScript, Vanilla CSS Glassmorphism UI)
* **Database:** `PostgreSQL` via Docker with the `pgvector` extension.

---

## 🛠️ Viewing the Database (Docker DB)

All document embeddings are stored inside your local Docker PostgreSQL container inside the `document_chunks` table.

**How to inspect the database:**
1. You can use any SQL graphical client like **DBeaver**, **pgAdmin**, or **DataGrip**.
2. Connect using the credentials specified in your `backend/.env` file:
   * **Host:** `localhost`
   * **Port:** `5432`
   * **Database Name:** `smart_search`
   * **Username:** `user`
   * **Password:** `password`
3. Expand your schemas and open the `document_chunks` table. You will physically see the `filename` string, the `chunk_text`, and the massive 3072-digit `embedding` array for each paragraph loaded!

---

## 📦 Installation & Setup Guide

### 1. Database (Docker)
Ensure your PostgreSQL `pgvector` container is running in Docker Desktop and ports are mapped to `5432`.
Run the database initializer script to create the necessary tables:
```bash
cd backend
python database.py
```

### 2. Backend Installation (FastAPI)
Navigate to the backend directory, initialize the environment, and install all libraries directly from `requirements.txt`:
```bash
cd backend
python -m venv venv 
.\venv\Scripts\activate 
pip install -r requirements.txt
```
To run the server:
```bash
uvicorn main:app --reload
```

### 3. Frontend Installation (React)
Open a new terminal and install the frontend packages.
```bash
cd frontend
npm install 
npm run dev
```
Open `http://localhost:5173` in your browser.