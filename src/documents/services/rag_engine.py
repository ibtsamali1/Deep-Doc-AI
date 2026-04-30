"""
RAG Engine — Core PDF processing and question-answering logic.

Uses:
    - PyPDFLoader for PDF text extraction
    - RecursiveCharacterTextSplitter for chunking
    - Google Gemini (via langchain-google-genai) for embeddings and LLM
    - FAISS for vector storage (persisted per-user to disk)
"""

import logging
from pathlib import Path

from django.conf import settings

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


# ─── Chunking configuration ───────────────────────────────────────────────────
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ─── RAG prompt template ──────────────────────────────────────────────────────
RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based on the provided context from PDF documents.

Use ONLY the following context to answer the question. If the answer is not found in the context, say "I could not find the answer in the uploaded documents."

Do not make up information. Be concise and accurate.

Context:
{context}

Question: {question}

Answer:"""


class RAGEngine:
    """
    Per-user RAG engine with FAISS persistence.

    Each user gets an isolated FAISS index directory so their documents
    are completely separate from other users.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.index_dir = Path(settings.FAISS_INDEX_DIR) / str(user_id)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def process_pdf(self, pdf_path: str, pdf_id: int) -> dict:
        """
        Extract text from a PDF, chunk it, generate embeddings,
        and merge into the user's FAISS index.

        Args:
            pdf_path: Absolute path to the PDF file on disk.
            pdf_id: Database ID of the UploadedPDF record (used as metadata).

        Returns:
            dict with 'num_pages' and 'num_chunks'.
        """
        logger.info("Processing PDF: user=%d, pdf_id=%d, path=%s", self.user_id, pdf_id, pdf_path)

        # Step 1: Load PDF pages
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        num_pages = len(pages)
        logger.info("Loaded %d pages from PDF", num_pages)

        # Step 2: Split into chunks
        chunks = self.text_splitter.split_documents(pages)

        # Step 3: Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata['pdf_id'] = pdf_id
            chunk.metadata['user_id'] = self.user_id
            chunk.metadata['chunk_index'] = i

        num_chunks = len(chunks)
        logger.info("Split into %d chunks", num_chunks)

        if num_chunks == 0:
            raise ValueError("No text could be extracted from the PDF. The file may be scanned/image-based.")

        # Step 4: Create or merge FAISS index
        self._merge_into_index(chunks)

        logger.info("PDF processed successfully: %d pages, %d chunks", num_pages, num_chunks)
        return {
            'num_pages': num_pages,
            'num_chunks': num_chunks,
        }

    def ask(self, question: str, pdf_id: int = None) -> dict:
        """
        Query the user's FAISS index and generate an answer using Gemini.

        Args:
            question: The user's question.
            pdf_id: Optional — filter results to a specific PDF.

        Returns:
            dict with 'answer' and 'sources'.
        """
        logger.info("Answering question: user=%d, pdf_id=%s, question='%s'", self.user_id, pdf_id, question[:100])

        # Load the persisted FAISS index
        db = self._load_index()
        if db is None:
            raise ValueError("No document index found. Please upload a PDF first.")

        # Perform similarity search
        k = 5  # number of relevant chunks to retrieve
        if pdf_id is not None:
            # Filter by specific PDF using FAISS metadata filtering
            docs = db.similarity_search(
                question,
                k=k,
                filter={"pdf_id": pdf_id},
            )
        else:
            docs = db.similarity_search(question, k=k)

        if not docs:
            return {
                'answer': 'No relevant content found in the uploaded documents for your question.',
                'sources': [],
            }

        # Build context from retrieved documents
        context = "\n\n---\n\n".join(doc.page_content for doc in docs)

        # Build and run the RAG chain
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        chain = prompt | self.llm | StrOutputParser()

        answer = chain.invoke({
            "context": context,
            "question": question,
        })

        # Build source references
        sources = []
        for doc in docs:
            sources.append({
                'pdf_id': doc.metadata.get('pdf_id'),
                'page': doc.metadata.get('page', 0) + 1,  # 1-indexed for display
                'snippet': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content,
            })

        logger.info("Generated answer with %d source chunks", len(sources))
        return {
            'answer': answer,
            'sources': sources,
        }

    def _merge_into_index(self, documents):
        """
        Create a new FAISS index from documents and merge with existing
        index if one exists. Then persist to disk.
        """
        new_db = FAISS.from_documents(documents, self.embeddings)

        existing_db = self._load_index()
        if existing_db is not None:
            existing_db.merge_from(new_db)
            self._save_index(existing_db)
            logger.info("Merged %d new documents into existing index", len(documents))
        else:
            self._save_index(new_db)
            logger.info("Created new index with %d documents", len(documents))

    def _load_index(self):
        """Load a persisted FAISS index from disk, or return None if not found."""
        index_path = self.index_dir / "index.faiss"
        if index_path.exists():
            return FAISS.load_local(
                str(self.index_dir),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        return None

    def _save_index(self, db):
        """Persist a FAISS index to the user's directory on disk."""
        db.save_local(str(self.index_dir))
        logger.info("Saved FAISS index to %s", self.index_dir)
