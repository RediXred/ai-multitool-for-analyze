from celery import shared_task
from .models import UploadedFile
import hashlib
import os
import logging
from baseanalyze.views import get_analysis_context

logger = logging.getLogger(__name__)

@shared_task
def analyze_uploaded_file(file_id):
    try:
        obj = UploadedFile.objects.get(id=file_id)
    except UploadedFile.DoesNotExist:
        logger.error(f"UploadedFile with id={file_id} does not exist.")
        return

    path = obj.file.path
    if not os.path.exists(path):
        logger.error(f"File not found at: {path}")
        return

    try:
        result = {
            'filename': os.path.basename(path),
            'size_bytes': os.path.getsize(path),
            'sha256': hash_file(path),
        }

        obj.result = result
        obj.analyzed = True
        obj.save()
        logger.info(f"Successfully analyzed: {path}")
        return file_id
    except Exception as e:
        logger.exception(f"Failed to analyze file {path}: {e}")

def hash_file(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

@shared_task
def analyze_file_task(file_id):
    file_obj = UploadedFile.objects.get(id=file_id)
    context = get_analysis_context(file_obj)