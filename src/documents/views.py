import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import UploadedPDF
from .services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

# Maximum upload size: 20 MB
MAX_UPLOAD_SIZE = 20 * 1024 * 1024


@csrf_exempt
@require_POST
def upload_pdf(request):
    """
    Upload and process a PDF file for RAG.

    Expects a multipart/form-data POST with a 'file' field containing the PDF.

    Returns JSON:
        {
            "status": "success",
            "pdf_id": <int>,
            "filename": <str>,
            "num_pages": <int>,
            "num_chunks": <int>,
            "message": "PDF processed successfully."
        }
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {'status': 'error', 'message': 'You must be logged in to upload files.'},
            status=401,
        )

    uploaded_file = request.FILES.get('file')

    if not uploaded_file:
        return JsonResponse(
            {'status': 'error', 'message': 'No file provided. Send a PDF file in the "file" field.'},
            status=400,
        )

    # Validate file type
    if not uploaded_file.name.lower().endswith('.pdf'):
        return JsonResponse(
            {'status': 'error', 'message': 'Only PDF files are accepted.'},
            status=400,
        )

    # Validate file size
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return JsonResponse(
            {'status': 'error', 'message': f'File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.'},
            status=400,
        )

    # Save the PDF record
    pdf_record = UploadedPDF(
        user=request.user,
        file=uploaded_file,
        original_filename=uploaded_file.name,
    )
    pdf_record.save()

    try:
        # Process the PDF through the RAG engine
        engine = RAGEngine(user_id=request.user.id)
        result = engine.process_pdf(
            pdf_path=pdf_record.file.path,
            pdf_id=pdf_record.id,
        )

        # Update the record with processing results
        pdf_record.num_pages = result['num_pages']
        pdf_record.num_chunks = result['num_chunks']
        pdf_record.is_processed = True
        pdf_record.save()

        logger.info(
            "PDF processed: user=%s, pdf_id=%d, pages=%d, chunks=%d",
            request.user.username, pdf_record.id, result['num_pages'], result['num_chunks'],
        )

        return JsonResponse({
            'status': 'success',
            'pdf_id': pdf_record.id,
            'filename': pdf_record.original_filename,
            'num_pages': result['num_pages'],
            'num_chunks': result['num_chunks'],
            'message': 'PDF processed successfully.',
        })

    except Exception as e:
        logger.exception("Failed to process PDF: %s", str(e))
        # Clean up the file if processing fails
        pdf_record.delete()
        return JsonResponse(
            {'status': 'error', 'message': f'Failed to process PDF: {str(e)}'},
            status=500,
        )


@csrf_exempt
@require_POST
def ask_question(request):
    """
    Ask a question about uploaded PDF documents.

    Expects a JSON POST body:
        {
            "question": "What is the main topic?",
            "pdf_id": 1  (optional — if omitted, searches all user's PDFs)
        }

    Returns JSON:
        {
            "status": "success",
            "question": <str>,
            "answer": <str>,
            "sources": [{"pdf_id": <int>, "page": <int>, "snippet": <str>}, ...]
        }
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid JSON in request body.'},
            status=400,
        )

    question = body.get('question', '').strip()
    pdf_id = body.get('pdf_id')

    if not request.user.is_authenticated:
        return JsonResponse(
            {'status': 'error', 'message': 'You must be logged in to ask questions.'},
            status=401,
        )

    if not question:
        return JsonResponse(
            {'status': 'error', 'message': 'The "question" field is required and cannot be empty.'},
            status=400,
        )

    # If a specific pdf_id is given, verify it belongs to this user
    if pdf_id is not None:
        if not UploadedPDF.objects.filter(id=pdf_id, user=request.user, is_processed=True).exists():
            return JsonResponse(
                {'status': 'error', 'message': f'PDF with id {pdf_id} not found or not yet processed.'},
                status=404,
            )

    # Check that the user has at least one processed PDF
    if not UploadedPDF.objects.filter(user=request.user, is_processed=True).exists():
        return JsonResponse(
            {'status': 'error', 'message': 'No processed PDFs found. Please upload a PDF first.'},
            status=404,
        )

    try:
        engine = RAGEngine(user_id=request.user.id)
        result = engine.ask(question=question, pdf_id=pdf_id)

        return JsonResponse({
            'status': 'success',
            'question': question,
            'answer': result['answer'],
            'sources': result['sources'],
        })

    except Exception as e:
        logger.exception("Failed to answer question: %s", str(e))
        return JsonResponse(
            {'status': 'error', 'message': f'Failed to generate answer: {str(e)}'},
            status=500,
        )
