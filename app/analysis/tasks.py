from celery import shared_task
from .models import UploadedFile
import hashlib
import os

@shared_task
def analyze_uploaded_file(file_id):
    obj = UploadedFile.objects.get(id=file_id)
    path = obj.file.path

    result = {
        'filename': os.path.basename(path),
        'size_bytes': os.path.getsize(path),
        'sha256': hash_file(path),
    }

    obj.result = result
    obj.analyzed = True
    obj.save()

def hash_file(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
