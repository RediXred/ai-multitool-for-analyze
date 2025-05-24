from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from analysis.models import UploadedFile
from .utils.file_utils import get_file_info, calculate_hashes


@login_required
def analyze_file(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    file_info = get_file_info(file_obj.file.path)
    file_info['hashes'] = calculate_hashes(file_obj.file.path)

    context = {
        'file': file_obj,
        'file_info': file_info,
    }

    return render(request, 'baseanalyze/analyze.html', context)

