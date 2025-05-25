from celery import shared_task
from django.core.files.storage import default_storage
import logging
from .utils.vt_utils import analyze_with_vt
from analysis.models import UploadedFile

logger = logging.getLogger(__name__)

@shared_task
def analyze_file_vt(file_path, file_id):
    try:
        if not default_storage.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {'error': 'File not found'}

        result = analyze_with_vt(file_path)
        
        file_obj = UploadedFile.objects.get(id=file_id)
        file_obj.vt_result = result
        file_obj.vt_status = 'completed' if not result.get('error') else 'failed'
        file_obj.save()
        
        logger.info(f"VirusTotal analysis completed for file ID {file_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in analyze_file_vt for file ID {file_id}: {str(e)}")
        return {'error': f'Task failed: {str(e)}'}