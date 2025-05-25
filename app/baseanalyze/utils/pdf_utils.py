from pdfminer.high_level import extract_text
import pdfid

def analyze_pdf(filepath):
    result = {}
    
    # Анализ структуры PDF
    with open(filepath, 'rb') as f:
        pdf_analysis = pdfid.PDFiD(f)
        result['pdfid_analysis'] = pdf_analysis.getStats()
    
    # Извлечение текста
    try:
        result['text'] = extract_text(filepath)[:5000]  # первые 5000 символов
    except:
        result['text'] = "Не удалось извлечь текст"
    
    return result