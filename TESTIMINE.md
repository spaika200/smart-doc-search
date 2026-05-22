# 🎓 Nutikas Dokumentide Otsingusüsteem — Automaattestide Juhend (TESTING)

See dokument annab lõputöö hindamiskomisjonile ja retsensendile põhjaliku ülevaate süsteemi automaattestidest, nende käivitamisest ning koodi kaetuse (**Code Coverage**) tulemustest.

Rakenduse töökindluse tagamiseks on loodud terviklik testraamistik, mis katab **93%** kogu serveripoolsest koodist (**Backend**). Testimiseks kasutatakse Pythoni standardset `unittest` raamistikku ja `coverage` teeki koodikaetuse analüüsiks.

---

## 📈 Koodi Automaatne Kaetus (Code Coverage)

Kõik testid on kirjutatud **isoleeritud (mockitud) keskkonnas**. See tähendab, et testide käivitamiseks **ei ole vaja** aktiivset Google Gemini API võtit ega töötavat PostgreSQL Docker konteinerit. Testid imiteerivad andmebaasi ja tehisintellekti vastuseid, tagades testraamistiku kiiruse ja sõltumatuse väliskeskkonnast.

### Koodikaetuse Aruanne (`coverage report`):

| Faili Nimi | Kirjeldus | Ridade arv | Katvuse protsent |
| :--- | :--- | :---: | :---: |
| **`database.py`** | Andmebaasi ühendus ja tabelite/skeemi initsialiseerimine. | 20 | **90%** 🟢 |
| **`document_loader.py`** | PDF, DOCX ja TXT failide parsijad ja tekstituvastus. | 32 | **88%** 🟢 |
| **`embedder.py`** | Vektor-manuste genereerimine ja andmebaasi bulk-salvestus. | 20 | **95%** 🟢 |
| **`vector_search.py`** | RAG-ahela otsingupäringud, ajalugu ja erinevad tooni režiimid. | 49 | **94%** 🟢 |
| **`main.py`** (API) | FastAPI ruutingud, CRUD otspunktid, veahaldused, limiidikaitse. | 168 | **85%** 🟢 |
| **`text_processor.py`** | Teksti tükeldamise (chunking) algoritmid. | 9 | **67%** 🟡 |
| **`tests.py`** | Automaattestide sviit. | 248 | **99%** 🟢 |
| **KOKKU (TOTAL)** | **Kogu Backend rakenduse testide katvus** | **546** | **93%** 🏆 |

---

## 🚀 Kuidas Teste Käivitada (Hindamisjuhend Komisjonile)

Testide ja koodikaetuse raporti käivitamiseks oma kohalikus masinas järgige järgmisi samme:

### 1. Virtuaalkeskkonna aktiveerimine
Veenduge, et olete `backend/` kaustas ning virtuaalkeskkond on aktiveeritud:
```bash
cd backend
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Lihtsate unittestide käivitamine
Kõikide testide jooksmiseks (ilma koodikaetuse raportita):
```bash
python tests.py
```
*Kõik 29 testi peaksid läbima edukalt ligikaudu **1.5 sekundiga**.*

### 3. Koodikaetuse mõõtmine ja raporti genereerimine
Kui soovite mõõta täpset koodiridade kaetust protsentides:

*   **Samm A: Käivitage testid katvuse analüsaatoriga:**
    ```bash
    python -m coverage run -m unittest tests.py
    ```
*   **Samm B: Kuvage raport konsoolis:**
    ```bash
    python -m coverage report
    ```
*   **Samm C: Genereerige klikitav ja visuaalne HTML-raport:**
    ```bash
    python -m coverage html
    ```
    *See käsk tekitab `backend/` kausta kataloogi nimega `htmlcov/`. Avage seal asuv fail `index.html` mis tahes veebibrauseris, et näha koodi katvust ridade ja failide kaupa eraldi.*

---

## 🔍 Mida ja Kuidas Testitakse?

Loodud automaattestid on jaotatud seitsmesse loogilisse kategooriasse:

### 1. `TestTextProcessor` (Teksti töötlemine)
*   **`test_text_splitting_returns_list`**: Kontrollib, et tükeldamise algoritm tagastab listi.
*   **`test_text_splitting_correct_chunks`**: Kontrollib, et pikk tekst (üle 1000 märgi) jaotatakse korrektselt mitmeks tükiks koos määratud ülekattega (overlap).
*   **`test_text_splitting_short_text`**: Kontrollib, et lühike tekst jääb ühte tükki.
*   **`test_empty_string_handling`**: Kontrollib tühjade andmete veakindlat käitlemist.

### 2. `TestVectorEmbeddings` (Vektor-manused)
*   **`test_gemini_vector_dimensions`**: Kontrollib, et vektoriseerija genereerib täpselt 3072-dimensionaalse vektori.
*   **`test_vectorization_type`**: Kontrollib, et vektori elemendid on ujukomaarvud (`float`), mis on pgvector andmebaasi ja koosinussarnasuse leidmise aluseks.

### 3. `TestDatabase` (Andmebaasi skeem)
*   **`test_postgres_pgvector_connection`**: Valideerib andmebaasi ühenduse loomise edukuse.
*   **`test_init_db`**: Testib andmebaasi tabelite (`document_chunks`, `chats`, `chat_messages`) ja `pgvector` laienduse korrektset loomist.

### 4. `TestDocumentLoader` (Failide parsijad)
*   **`test_extract_text_from_txt`**: Testib tavalise `.txt` faili sisselugemist.
*   **`test_extract_text_from_docx`**: Testib Wordi `.docx` faili parsijat ja teksti kättesaamist.
*   **`test_extract_text_from_pdf`**: Testib PDF faili parsijat ja lehekülgede kaupa läbikäimist.
*   **`test_extract_text_invalid_extension`**: Tagab, et süsteem keeldub mittetoetatud formaatidest (nt `.exe`), tagastades tühja vastuse.
*   **`test_extract_text_missing_file`**: Tagab veakindla käitumise, kui faili füüsiliselt kettal ei eksisteeri.

### 5. `TestEmbedder` (Vektoriseerimine ja Salvestamine)
*   **`test_process_and_save_chunks`**: Testib kogu faili vektoriseerimise ahelat ja selle edukat SQL-salvestust vektorandmebaasi.

### 6. `TestRAGPipeline` (Tehisintellekti loogika & Hallutsinatsioonid)
*   **`test_rag_correct_answer_from_context`**: Testib, et AI suudab etteantud dokumendikontekstist leida korrektse vastuse ja viidata õigele failinimele.
*   **`test_rag_hallucination_prevention`**: **Kõige olulisem test!** Tõendab, et kui andmebaasist vasteid ei leita, keeldub AI vastust välja mõtlemast ja tagastab eestikeelse turvalise veateate (*"Vabandust, aga andmebaasist ei leitud teavet..."*).
*   **`test_query_vector_db`**: Valideerib andmebaasi päringu moodustamist ja koosinussarnasuse (`<=>`) operaatori tööd.
*   **`test_generate_rag_response_with_history_and_tones`**: Testib vestluse ajaloo korrektset kaasamist ja kõigi nelja AI tooni (tavaline, lihtne, lühike, juriidiline) käitumist.

### 7. `TestFastAPIEndpoints` (API ja Integratsioon)
*   **`test_read_root`**: Valideerib tervituslehe kättesaadavust.
*   **`test_health_check_online` / `test_health_check_offline`**: Testib API terviseindikaatorit ja veateateid juhul, kui andmebaasi ühendus puudub.
*   **`test_chats_crud_endpoints`**: Testib vestluste täielikku loomise, muutmise, kuvamise ja kustutamise tsüklit.
*   **`test_chat_messages_endpoint`**: Testib vestluse sõnumite ajaloo pärimist andmebaasist.
*   **`test_documents_endpoints`**: Testib andmebaasis olevate dokumentide kuvamist ja dokumentide kustutamise cascade-funktsionaalsust.
*   **`test_ask_question_rate_limit`**: Testib API veatuvastust juhul, kui tasuta Gemini API limiidid on täitunud (429 RESOURCE_EXHAUSTED viga), tagades kasutajale viisaka veateate.
