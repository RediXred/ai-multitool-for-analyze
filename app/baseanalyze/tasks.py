from celery import shared_task
from django.core.files.storage import default_storage
import logging
from .utils.vt_utils import analyze_with_vt
from analysis.models import UploadedFile
from .utils.ai_utils import ai_analyze

logger = logging.getLogger(__name__)

@shared_task
def analyze_file_vt(file_path, file_id, strings, pe_info):
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
        analyze_file_ai.delay(file_path, file_id, strings, pe_info)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_file_vt for file ID {file_id}: {str(e)}")
        analyze_file_ai.delay(file_path, file_id, strings, pe_info)
        return {'error': f'Task failed: {str(e)}'}


@shared_task
def analyze_file_ai(file_path, file_id, strings, pe_info):
    try:
        file_obj = UploadedFile.objects.get(id=file_id)

        #strings = extract_strings(file_path)
        #pe_info = analyze_pe_file(file_path)
        imports = pe_info.get('imports', [])
        exports = pe_info.get('exports', [])
        vt_info = file_obj.vt_result or {}

        ai_result = ai_analyze(file_path, strings, imports, exports, vt_info)

        file_obj.ai_result = ai_result
        file_obj.ai_status = 'completed' if ai_result != 'error' else 'failed'
        file_obj.save()

        logger.info(f"AI analysis completed for file ID {file_id}")
        return ai_result

    except Exception as e:
        logger.error(f"AI analysis failed for file ID {file_id}: {str(e)}")
        try:
            file_obj = UploadedFile.objects.get(id=file_id)
            file_obj.ai_result = {'error': str(e)}
            file_obj.ai_status = 'failed'
            file_obj.save()
        except:
            pass
        return {'error': str(e)}