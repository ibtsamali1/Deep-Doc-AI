from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload-pdf/', views.upload_pdf, name='upload-pdf'),
    path('ask/', views.ask_question, name='ask'),
]
