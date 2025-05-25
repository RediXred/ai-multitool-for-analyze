import os
import magic
import hashlib

def get_file_info(file_path):
    file_info = {
        'name': os.path.basename(file_path),
        'size': f"{os.path.getsize(file_path) / 1024:.2f} KB",
        'mime_type': magic.from_file(file_path),
        'magic_bytes': magic.from_file(file_path, mime=True),
    }
    return file_info

def calculate_hashes(filepath):
    hashes = {}
    with open(filepath, 'rb') as f:
        data = f.read()
        for algo in ['md5', 'sha1', 'sha256', 'sha512']:
            hashes[algo] = getattr(hashlib, algo)(data).hexdigest()
    return hashes