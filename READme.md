# 🎓 Dokumentide Intelligentne Otsingusüsteem (Smart Document Search)

**Lõputöö Autorid:** Artjom Aristov & Nikita Žuravljov  
**Kool:** Ida-Virumaa Kutsehariduskeskus (JPTV22)  

See projekt on täislahendusena loodud **RAG (Retrieval-Augmented Generation)** süsteem. Rakendus võimaldab kasutajal üles laadida dokumente, mis muudetakse vektorkujule, ning seejärel esitada nende põhjal küsimusi. Süsteem on ehitatud nii, et AI (Gemini) vastab küsimustele **ainult** üleslaaditud dokumentide põhjal, välistades hallutsinatsioonid.

---

## 📂 Projekti Struktuur

```
smart-doc-search/
├── backend/                    # FastAPI server + RAG pipeline
│   ├── main.py                # API endpoints
│   ├── database.py            # PostgreSQL schema
│   ├── embedder.py            # Gemini embeddings
│   ├── vector_search.py       # RAG pipeline
│   ├── document_loader.py     # File parsing (PDF, DOCX, TXT)
│   ├── text_processor.py      # Text chunking
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx            # Main component
│   │   ├── App.css            # Styling
│   │   └── index.css          # Global styles + themes
│   ├── package.json           # Node dependencies
│   └── vite.config.js         # Build config
│
└── README.md                  # This file
```

---

## 🔗 API Endpoint Ülevaade

| Meetod | Endpoint | Eesmärk |
|--------|----------|---------|
| `GET` | `/health/` | Andmebaasi ühenduse staatus |
| `POST` | `/upload/` | Dokumendi üleslaadimine ja indekseerimine |
| `POST` | `/ask/` | **Core**: RAG query - küsimuse esitamine |
| `POST` | `/chats/` | Uue vestluse loomine |
| `GET` | `/chats/` | Kõik vestlused |
| `GET` | `/chats/{id}/messages` | Vestluse sõnumid |
| `PUT` | `/chats/{id}` | Vestluse pealkirja muutmine |
| `DELETE` | `/chats/{id}` | Vestluse kustutamine |
| `GET` | `/documents/` | Kõik indekseeritud dokumendid |
| `DELETE` | `/documents/{filename}` | Dokumendi kustutamine |

---

## 🌟 Süsteemi Võimalused ja Uuendused

Süsteem sisaldab professionaalsel tasemel kasutajaliidest (Glassmorphism) ja ettevõtte tasemel andmebaasilahendust:

- 📄 **Dokumentide tugi:** `.pdf`, `.docx` ja `.txt` failide üleslaadimine lokaalsesse PostgreSQL vektorandmebaasi.
- 🛡️ **Hallutsinatsioonide Vältimine (Enterprise-Grade RAG):** Süsteem on ehitatud vastama *ainult* üleslaaditud dokumentide põhjal. Kui vastust ei leidu, keeldub AI seda välja mõtlemast.
- 🎯 **Täpne Allikaviitamine:** AI vastuste juures on klikitavad allikaviited (📄), mis avavad modaali näidates täpset teksti, mida tehisintellekt luges.
- 💬 **Dünaamiline Vestluse Ajalugu:** Kõik vestlused salvestatakse andmebaasi. Vestlusi saab ümber nimetada ja kustutada.
- 🌓 **Tume / Hele Režiim (Dark/Light Mode):** Kasutajaliides toetab täielikult teemade vahetamist, salvestades eelistuse brauseri mällu.
- 📊 **Reaalajas Üleslaadimise Indikaator:** Suurte dokumentide puhul kuvatakse reaalajas edenemisriba (0-100%).
- ✨ **Animatsioonid ja Markdown:** Markdowni tugi (tabelid, koodiplokid, tsitaadid) ning "põrkavate punktide" (bouncing dots) animatsioon, kui AI genereerib vastust.
- 🎭 **Tooni Kontroll:** Võimalus valida AI vastamisstiili ("Tavaline", "Lihtne keel", "Lühikokkuvõte", "Juriidiline").
- 💾 **Eksportimine:** Kogu vestlus on võimalik alla laadida `.txt` failina.
- 🟢 **Süsteemi Tervise Jälgimine:** Visuaalne indikaator näitab reaalajas, kas andmebaasi ühendus on aktiivne.
- ⚡ **API Limiidikaitsed:** Sisseehitatud veahaldus, mis kaitseb süsteemi Gemini API tasuta paketi päringulimiitide ületamise eest, pakkudes kasutajale viisakat veateadet.

---

## 🚀 Tehnoloogiad ja AI Mudelid

Süsteem on jaotatud kolmeks peamiseks osaks:

### 1. AI Arhitektuur (Google Gemini API)
* **Vektori Mudel:** `models/gemini-embedding-001` (Muudab dokumendi teksti 3072-dimensionaalseks vektoriks).
* **Generatiivne Mudel:** `models/gemini-2.5-flash` (Analüüsib vektoreid ja genereerib eestikeelse vastuse).

### 2. Back-end (Python & FastAPI)
* API päringute töötlemine.
* Dokumentide parsijad (`pypdf`, `python-docx`).
* LangChain teksti tükeldamiseks ja vektoriseerimiseks.

### 3. Front-end (React & Vite)
* SPA (Single Page Application) arhitektuur.
* Vanilla CSS Glassmorphism stiil koos Light/Dark režiimiga.

### 4. Andmebaas (PostgreSQL & pgvector)
* Lokaalne Docker konteiner, mis kasutab `pgvector` laiendust vektorotsingu (koosinussarnasuse) teostamiseks.

---

## 📦 Paigaldamise ja Käivitamise Juhend (Komisjonile)

Süsteemi testimiseks lokaalses masinas palun jälgige järgnevaid samme:

### 1. Keskkonnamuutujad (.env)
Loo `backend` kausta fail nimega `.env` ja lisa sinna järgmised andmed:
```env
GOOGLE_API_KEY=sinu_gemini_api_võti_siia
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=smart_search
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```
*(Märkus: Tasuta Gemini API võtme saate genereerida aadressilt: [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 2. Backend-i Paigaldus (Python & Sõltuvused)
Liigu `backend` kausta, loo virtuaalkeskkond (venv) ja installeeri vajalikud teegid:
```bash
cd backend
python -m venv venv 
.\venv\Scripts\activate 
pip install -r requirements.txt
```

### 3. Andmebaasi Initsialiseerimine (Docker)
Veendu, et sinu PostgreSQL `pgvector` konteiner jookseb Dockeris (pordil 5432).
Kuna sõltuvused (sh `psycopg2`) on nüüd installeeritud, saad luua vajalikud andmebaasi tabelid:
```bash
python database.py
```

### 4. Serveri Käivitamine (FastAPI)
Veendu, et oled `backend` kaustas ja virtuaalkeskkond (`venv`) on aktiivne, seejärel käivita API:
```bash
uvicorn main:app --reload
```

### 4. Frontend-i Käivitamine (React)
Avage uus terminali aken ja liikuge `frontend` kausta:
```bash
cd frontend
npm install
npm run dev
```
Rakendus on nüüd kättesaadav brauseris aadressil: **http://localhost:5173**

### 5. Automaattestide ja Koodikaetuse (Code Coverage) Käivitamine
Süsteemi stabiilsust ja funktsionaalsust testitakse põhjalikult 29 automaattestiga, mis tagavad **93%** koodikaetuse. Testid on isoleeritud ja käivituvad vähem kui 2 sekundiga ilma väliseid API-sid või andmebaase nõudmata.

Põhjaliku automaattestide ja koodikaetuse juhendi leiate eraldi failist:
👉 **[TESTIMINE.md](TESTIMINE.md)**

Kiireks testide käivitamiseks:
```bash
cd backend
python tests.py
```

---

## 🛠️ Andmebaasi Struktuur
Kui soovite süsteemi sisu visuaalselt kontrollida (nt DBeaver või pgAdmin abil):
* **`document_chunks` tabel:** Sisaldab failinime, teksti ja 3072-kohalist vektorit.
* **`chats` tabel:** Sisaldab vestluste ajalugu ja pealkirju.
* **`chat_messages` tabel:** Sisaldab kasutaja ja AI sõnumeid, sealhulgas allikaviidete JSON faile.
