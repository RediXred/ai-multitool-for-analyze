from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import os
import logging
from analysis.models import UploadedFile

# Create your views here.
logger = logging.getLogger(__name__)
@login_required(login_url='accounts:login')
def dashboard(request):
    files = request.user.uploaded_files.all().order_by('-uploaded_at')
    logger.warning(f"Files: {files}")
    #chats = request.user.chat.all().order_by('-created_at')
    return render(request, 'dashboard/dashboard.html', {'files': files})

@login_required(login_url='accounts:login')
def delete_file(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    if file.user != request.user:
        logger.warning(f"User {request.user.username} attempted to delete file {file.id} they do not own.")
        return redirect('dashboard:dashboard')
    if request.method == 'POST':
        if os.path.exists(file.file.path):
            os.remove(file.file.path)
        file.delete()
        logger.info(f"File {file.id} deleted by user {request.user.username}")
    return redirect('dashboard:dashboard')