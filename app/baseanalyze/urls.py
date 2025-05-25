from django.urls import path
from . import views

urlpatterns = [
    path('<int:file_id>/', views.analyze_file, name='analyze-file'),
]