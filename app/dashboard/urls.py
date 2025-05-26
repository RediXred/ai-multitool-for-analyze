from django.urls import path
from .views import dashboard, delete_file


app_name = 'dashboard'
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('delete/<int:pk>/', delete_file, name='delete_file'),
]
