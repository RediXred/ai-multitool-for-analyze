from stegano import lsb
from PIL import Image
import io

def check_steganography(filepath):
    try:
        with Image.open(filepath) as img:
            # Проверка LSB стеганографии
            hidden_data = lsb.reveal(filepath)
            return {
                'lsb_detected': hidden_data is not None,
                'hidden_data': hidden_data[:500] if hidden_data else None
            }
    except Exception:
        return {'lsb_detected': False, 'error': 'Not a supported image format'}