import requests
import io
from pypdf import PdfReader
import time

def download_and_parse_pdf(pdf_url: str, timeout: int = 30) -> str:
    """
    Download a PDF from arXiv and extract all text.
    Includes a 0.5s delay to respect arXiv rate limits.
    """
    try:
        time.sleep(0.5)  # Be polite to arXiv servers
        response = requests.get(pdf_url, timeout=timeout)
        if response.status_code != 200:
            return ""
        
        reader = PdfReader(io.BytesIO(response.content))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""