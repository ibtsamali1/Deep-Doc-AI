from django.contrib import admin
from .models import UploadedPDF


@admin.register(UploadedPDF)
class UploadedPDFAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'num_pages', 'num_chunks', 'is_processed', 'uploaded_at')
    list_filter = ('is_processed', 'uploaded_at', 'user')
    search_fields = ('original_filename', 'user__username')
    readonly_fields = ('num_pages', 'num_chunks', 'is_processed', 'uploaded_at')
    ordering = ('-uploaded_at',)
