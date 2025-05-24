from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import logging
# Create your views here.
logger = logging.getLogger(__name__)
@login_required(login_url='accounts:login')
def dashboard(request):
    files = request.user.uploaded_files.all().order_by('-uploaded_at')
    logger.warning(f"Files: {files}")
    #chats = request.user.chat.all().order_by('-created_at')
    return render(request, 'dashboard/dashboard.html', {'files': files})