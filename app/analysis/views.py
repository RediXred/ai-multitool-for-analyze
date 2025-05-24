from django.shortcuts import render, redirect, get_object_or_404
from .forms import FileUploadForm
from .models import UploadedFile
from .tasks import analyze_uploaded_file
from django.http import HttpResponse

# Create your views here.
def upload_file(requests):
    if requests.method == 'POST':
        form = FileUploadForm(requests.POST, requests.FILES)
        if form.is_valid():
            file = form.save()
            analyze_uploaded_file.delay(file.pk)
            return redirect('analysis:home')
    else:
        form = FileUploadForm()
    return render(requests, 'analysis/upload.html', {'form': form})

def upload_success(request, pk):
    file = get_object_or_404(UploadedFile, pk=pk)
    return render(request, 'analysis/success.html', {'file': file})

def home(request):
    return HttpResponse("Multitool: домашняя страница.")