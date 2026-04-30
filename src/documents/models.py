from django.db import models
from django.contrib.auth.models import User


class UploadedPDF(models.Model):
    """Tracks PDF files uploaded by authenticated users for RAG processing."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_pdfs',
        help_text='The user who uploaded this PDF.',
    )
    file = models.FileField(
        upload_to='pdfs/%Y/%m/%d/',
        help_text='The uploaded PDF file.',
    )
    original_filename = models.CharField(
        max_length=255,
        help_text='Original filename as uploaded by the user.',
    )
    num_pages = models.IntegerField(
        default=0,
        help_text='Number of pages extracted from the PDF.',
    )
    num_chunks = models.IntegerField(
        default=0,
        help_text='Number of text chunks after splitting.',
    )
    is_processed = models.BooleanField(
        default=False,
        help_text='Whether embeddings have been generated and stored.',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Uploaded PDF'
        verbose_name_plural = 'Uploaded PDFs'

    def __str__(self):
        return f"{self.original_filename} ({self.user.username})"
