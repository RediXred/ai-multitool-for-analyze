import pefile
import requests



def analyze_pe_file(filepath):
    try:
        pe = pefile.PE(filepath)
    except pefile.PEFormatError:
        return {'error': 'Not a valid PE file'}

    result = {}

    result['machine'] = hex(pe.FILE_HEADER.Machine)
    result['number_of_sections'] = pe.FILE_HEADER.NumberOfSections
    result['entry_point'] = hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)

    result['entry_point'] = hex(pe.OPTIONAL_HEADER.ImageBase + pe.OPTIONAL_HEADER.AddressOfEntryPoint)

    result['sections'] = []
    for section in pe.sections:
        result['sections'].append({
            'name': section.Name.decode(errors='ignore').strip('\x00'),
            'virtual_address': hex(section.VirtualAddress),
            'virtual_size': hex(section.Misc_VirtualSize),
            'raw_size': hex(section.SizeOfRawData),
        })

    result['imports'] = []
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll = entry.dll.decode(errors='ignore')
            for imp in entry.imports:
                result['imports'].append({
                    'dll': dll,
                    'name': imp.name.decode(errors='ignore') if imp.name else None,
                    'address': hex(imp.address),
                })

    result['exports'] = []
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            result['exports'].append({
                'name': exp.name.decode(errors='ignore') if exp.name else None,
                'address': hex(pe.OPTIONAL_HEADER.ImageBase + exp.address),
            })

    return result

