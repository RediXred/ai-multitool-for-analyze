import requests
import os
import time
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_with_vt(filepath):
    API_KEY = os.getenv('VT_API_KEY')
    if not API_KEY:
        return {'error': 'VT_API_KEY is not set'}

    upload_url = 'https://www.virustotal.com/api/v3/files'
    headers = {
        'x-apikey': API_KEY,
    }

    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(upload_url, headers=headers, files=files)
            response.raise_for_status()
    except requests.RequestException as e:
        return {
            'error': f'Upload failed: {str(e)}',
            'details': response.text if 'response' in locals() else 'No response'
        }

    analysis_id = response.json()['data']['id']
    logger.info(f"File uploaded, analysis ID: {analysis_id}")

    analysis_url = f'https://www.virustotal.com/api/v3/analyses/{analysis_id}'
    max_attempts = 20
    poll_interval = 10
    for attempt in range(max_attempts):
        try:
            result_response = requests.get(analysis_url, headers=headers)
            result_response.raise_for_status()
        except requests.RequestException as e:
            if result_response.status_code == 429:
                logger.warning(f"Rate limit hit, retrying after {poll_interval * 2}s")
                time.sleep(poll_interval * 2)
                continue
            return {'error': f'Failed to get analysis: {str(e)}'}

        analysis_data = result_response.json()
        status = analysis_data['data']['attributes']['status']
        logger.info(f"Attempt {attempt + 1}/{max_attempts}: Analysis status: {status}")
        if status == 'completed':
            break
        time.sleep(poll_interval)
    else:
        return {'error': 'Analysis timeout'}

    file_id = analysis_data['meta']['file_info']['sha256']
    file_info_url = f'https://www.virustotal.com/api/v3/files/{file_id}'
    try:
        final_response = requests.get(file_info_url, headers=headers)
        final_response.raise_for_status()
        logger.info(f"Final report fetched for file ID: {file_id}")
        logger.debug(f"Final response: {final_response.json()}")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch final report: {str(e)}")
        return {
            'error': f'Could not fetch final report: {str(e)}',
            'details': final_response.text if 'final_response' in locals() else 'No response'
        }

    data = final_response.json().get('data', {})
    attributes = data.get('attributes', {})

    timestamp = attributes.get('last_analysis_date')
    scan_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat() if timestamp else None
    status = attributes.get('last_analysis_status', 'unknown')
    stats = attributes.get('last_analysis_stats', {})

    raw_results = attributes.get('last_analysis_results', {})
    detections = []
    for engine, result in raw_results.items():
        if result.get('category') != 'undetected':
            detections.append({
                'engine': result.get('engine_name'),
                'version': result.get('engine_version'),
                'updated': result.get('engine_update'),
                'method': result.get('method'),
                'category': result.get('category'),
                'result': result.get('result'),
            })

    result = {
        'scan_date': scan_date,
        'status': status,
        'stats': stats,
        'detections': detections,
        'permalink': f"https://www.virustotal.com/gui/file/{file_id}/detection"
    }
    logger.info(f"Returning VT result: {result}")
    return result