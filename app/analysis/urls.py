from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
    path('upload/success/<int:pk>/', views.upload_success, name='upload_success'),
    path('', views.home, name='home'),
]