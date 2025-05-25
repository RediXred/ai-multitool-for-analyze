import re

def extract_strings(filepath, min_length=4):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    strings = []
    for s in re.findall(b'[\x20-\x7E]{' + str(min_length).encode() + b',}', data):
        strings.append(s.decode('utf-8', errors='ignore'))
    
    return strings