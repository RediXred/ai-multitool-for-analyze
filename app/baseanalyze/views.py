from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from analysis.models import UploadedFile
from .utils.file_utils import get_file_info, calculate_hashes
from .utils.strings_utils import extract_strings
from .utils.pe_utils import analyze_pe_file
from .tasks import analyze_file_vt
from .utils.ai_utils import ai_analyze
import logging

logger = logging.getLogger(__name__)

def get_analysis_context(file_obj):
    # baseinfo
    file_info = get_file_info(file_obj.file.path)
    file_info['hashes'] = calculate_hashes(file_obj.file.path)

    # strings
    strings = extract_strings(file_obj.file.path)

    # peinfo
    pe_info = analyze_pe_file(file_obj.file.path)
    if 'imports' not in pe_info:
        pe_info['imports'] = []
    if 'exports' not in pe_info:
        pe_info['exports'] = []

    context = {
        'file': file_obj,
        'file_info': file_info,
        'strings': strings,
        'pe_info': pe_info,
    }

    if file_obj.vt_status not in ['pending', 'completed']:
        analyze_file_vt.delay(file_obj.file.path, file_obj.id, strings, pe_info)
        file_obj.vt_status = 'pending'
        file_obj.save()
        logger.info(f"Started async VT analysis for file ID {file_obj.id}")

    # vt_check
    if file_obj.vt_status == 'completed' and file_obj.vt_result:
        context['vt_info'] = file_obj.vt_result
    elif file_obj.vt_status == 'failed':
        context['vt_info'] = file_obj.vt_result or {'error': 'Analysis failed'}
    else:
        context['vt_info'] = {'error': 'Analysis in progress, please check back later.'}

    # ai_check
    if file_obj.ai_status == 'completed' and file_obj.ai_result:
        context['ai_info'] = file_obj.ai_result
    elif file_obj.ai_status == 'failed':
        context['ai_info'] = file_obj.ai_result or {'error': 'AI analysis failed'}
    else:
        context['ai_info'] = {'error': 'AI analysis in progress. Please check back later.'}

    return context


@login_required
def analyze_file(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    context = get_analysis_context(file_obj)
    return render(request, 'baseanalyze/analyze.html', context)
