# Deep Doc AI - Detailed Technical Documentation

## 1. Project Overview and Structure
Deep Doc AI is a Retrieval-Augmented Generation (RAG) web application. It allows users to upload PDF documents, intelligently indexes the text, and lets users ask questions to extract precise, context-aware answers using AI.

### Core Directories
- **`src/chat_rag/`**: The core Django project directory. Contains global `settings.py` and root `urls.py`.
- **`src/documents/`**: The main Django app handling logic.
  - **`models.py`**: Defines the `UploadedPDF` model linking files to the authenticated user.
  - **`views.py`**: Contains the API endpoints for uploading (`/api/upload-pdf/`) and asking questions (`/api/ask/`).
  - **`services/rag_engine.py`**: The core engine that orchestrates LangChain, FAISS, and Gemini APIs.
- **`templates/`**: Contains HTML templates. `base.html` is the root layout. `home.html` is the landing page. `allauth/` contains overridden login/signup templates.
- **`static/css/styles.css`**: The central stylesheet defining the pure Red/White/Black design system.

---

## 2. The Technology Stack
- **Web Framework:** **Django** (Handles routing, authentication, and API endpoints).
- **Authentication:** **Django Allauth** & **Django Allauth UI** (Tailwind CSS stylized forms).
- **AI Orchestration:** **LangChain** (Connects text extractors, vector databases, and LLMs).
- **Language Models (LLMs):** **Google Gemini API**.
- **Vector Database:** **FAISS** (Facebook AI Similarity Search) - a highly efficient local vector store.
- **PDF Extraction:** **PyPDFLoader** (Extracts raw text from PDF pages).

---

## 3. How the RAG Pipeline Works

Retrieval-Augmented Generation (RAG) bridges the gap between your private documents and a Large Language Model (LLM). 

### Step 1: Uploading and Chunking
When a user uploads a PDF, the file is read by `PyPDFLoader`. The text is extracted page by page. 
Because LLMs have context limits, we cannot feed an entire 500-page book at once. Instead, we divide the text into "Chunks".
- **Algorithm Used:** `RecursiveCharacterTextSplitter`.
- **Chunk Size:** 1,000 characters per chunk.
- **Chunk Overlap:** 200 characters. Overlapping ensures that if a sentence is split midway, the context is preserved across chunks.

### Step 2: Vectorization (Embeddings)
Each chunk of text is transformed into a mathematical vector (an array of numbers representing the semantic meaning of the text).
- **Embedding Model Used:** `models/gemini-embedding-001`.
- **Embedding Dimensions:** Gemini embeddings generate high-dimensional vectors (typically 768 dimensions).
- **API Calls:** 1 API call is made to Google to embed the batch of chunks extracted from the uploaded PDF.

### Step 3: Vector Storage
The vectors are stored locally using **FAISS**. 
- **Algorithm:** FAISS organizes vectors using index structures that allow for rapid nearest-neighbor search (L2 distance or Inner Product).
- **Data Isolation:** Each user has a unique FAISS index folder (`faiss_index/<user_id>`), ensuring strict privacy between different users' documents.

### Step 4: Asking a Question
When a user types a question in the chat:
1. **Query Embedding (1 API Call):** The user's question is sent to the `gemini-embedding-001` model to be converted into a vector.
2. **Similarity Search:** FAISS compares the question's vector against all the document vectors. It retrieves the top `k` (usually 4) most similar chunks.
3. **Answer Generation (1 API Call):** The retrieved chunks are injected into a strict prompt template alongside the user's question. This prompt is sent to the LLM.
   - **LLM Used:** `models/gemini-2.5-flash` (Fast, cost-effective, and highly intelligent).
   - **Temperature:** Set to `0.3` to keep the model grounded and factual, preventing hallucinations.

---

## 4. Understanding API Consumption

For every **PDF Upload**:
- **1 Batch API Call** to Google Generative AI to embed all the text chunks.

For every **Chat Question**:
- **1 API Call** to embed the text of the user's question.
- **1 API Call** to `gemini-2.5-flash` to generate the final textual answer based on the retrieved context.

---

## 5. Helpful Commands for Beginners

Here are the commands you need to understand and operate the project:

**Starting the Virtual Environment:**
```bash
# Windows
venv\Scripts\activate
# MacOS/Linux
source venv/bin/activate
```

**Installing Required Packages:**
```bash
pip install -r requirement.txt
```

**Applying Database Changes:**
Whenever you modify `models.py` (like adding a new field to the database), you must run:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Running the Server:**
Starts the local development server on `http://127.0.0.1:8000`.
```bash
python manage.py runserver
```

**Creating an Admin User:**
Allows you to log into `http://127.0.0.1:8000/admin/` to view raw database records.
```bash
python manage.py createsuperuser
```
