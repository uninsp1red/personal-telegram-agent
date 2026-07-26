import pytesseract
from PIL import Image


def extract_text(image_path: str) -> str:
    """Чистый OCR, без LLM. lang='rus+eng' — иначе кириллица не читается вообще."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang="rus+eng")