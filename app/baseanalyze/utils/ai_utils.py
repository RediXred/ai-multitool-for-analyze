from google import genai
import os
from .strings_utils import extract_strings
import logging

logger = logging.getLogger(__name__)

def ai_analyze(filepath, strings, imports, exports, vt_info):
    
    client = genai.Client(api_key=os.getenv('GEMENI_API_KEY'))

    combined_text = "\n".join(strings)
    combined_text = combined_text[:2000] + "..."

    prompt = f"""
        You are a cybersecurity analyst AI. Analyze the following extracted strings from a potentially suspicious binary file:

        {combined_text}

        and modules from this file:
        {imports}, {exports}.

        Also, when assessing the risk, rely on the result of the VirusTotal analysis:
        {vt_info}

        Based on these strings, modules and VT, provide a concise security analysis. Your response must include the following:

        1. **General Summary** – What does the file appear to do, based on the strings/modules?
        2. **Suspicious Indicators** – Any signs of malicious behavior (e.g., use of network functions, DLLs, suspicious keywords)?
        3. **Potential Functionality** – Could this be malware, a dropper, keylogger, backdoor, etc.?
        4. **Notable Strings** – List 3–5 notable or interesting strings with a short explanation.
        5. **Risk Assessment** – Low / Medium / High risk based on the evidence.

        Keep the response clear and not long.
        """


    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text