# Deep Doc AI

Deep Doc AI is a powerful, context-aware Retrieval-Augmented Generation (RAG) system built with Django. It allows users to securely upload PDF documents, automatically index their contents, and ask natural language questions to extract precise, cited answers using Google's advanced Gemini AI models.

## Features

- **Intelligent Q&A:** Chat directly with your documents. The RAG engine scans your specific PDF and uses `gemini-2.5-flash` to generate accurate answers based *only* on the text provided.
- **Source Citations:** Every answer includes the exact source page numbers from your document so you can instantly verify facts.
- **Document Processing:** Securely upload PDFs (up to 20MB). The system uses LangChain and FAISS to extract text, chunk it intelligently, and generate high-quality vector embeddings locally.
- **User Authentication:** Complete user management (Sign Up, Sign In, Password Reset) built securely with `django-allauth` and stylized with modern Tailwind CSS forms.
- **Modern UI:** A striking, responsive, pure Red/White/Black brutalist aesthetic designed for speed, clarity, and ease of use.
- **Persistent Storage:** Document vectors are stored efficiently via FAISS on a per-user basis, ensuring privacy and eliminating the need to re-process files.

## Tech Stack

- **Backend:** Python, Django
- **Authentication:** Django Allauth, Django Allauth UI (Tailwind CSS)
- **AI & RAG:** LangChain, FAISS (Local Vector Database), PyPDF
- **LLMs:** Google Gemini API (`gemini-2.5-flash` for generation, `gemini-embedding-001` for vectorization)
- **Frontend:** HTML5, Vanilla CSS/JS

## Setup & Installation

### Prerequisites

- Python 3.10+
- Google Gemini API Key

### 1. Clone the Repository

```bash
git clone <repository_url>
cd Document_Intelligence_Chat_System
```

### 2. Create a Virtual Environment & Install Dependencies

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirement.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory (where `manage.py` is located) and add your Google Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Database Migrations

Apply the initial database migrations to set up the authentication and document tracking models:

```bash
cd src
python manage.py migrate
```

### 5. Run the Server

Start the Django development server:

```bash
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000` to create an account and start chatting with your PDFs!

## Project Structure

- `src/chat_rag/`: Main Django project configuration, settings, and URLs.
- `src/documents/`: Core application handling PDF uploads, FAISS vector indexing, and the LangChain RAG engine.
- `templates/`: HTML templates including the global base, landing page, and overridden authentication layouts.
- `static/css/`: Global stylesheets defining the custom design system.
