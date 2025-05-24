from django.shortcuts import render, redirect, get_object_or_404
from .forms import FileUploadForm
from .models import UploadedFile
from .tasks import analyze_uploaded_file
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user
            uploaded_file.save()
            analyze_uploaded_file.delay(uploaded_file.id)
            return redirect('dashboard')
    else:
        form = FileUploadForm()
    return render(request, 'analysis/upload.html', {'form': form})

def upload_success(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    return render(request, 'analysis/success.html', {'file': file})

def home(request):
    return HttpResponse("Multitool: домашняя страница.")