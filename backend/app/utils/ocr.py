import io
import os
import logging

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

# Try to configure Tesseract path if available
TESSERACT_AVAILABLE = False
POPPLER_AVAILABLE = False

try:
    import pytesseract
    tesseract_path = os.getenv("TESSERACT_PATH")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    # Quick check if tesseract is callable
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
except Exception:
    logger.warning("Tesseract not available - scanned PDF/image OCR disabled")

try:
    from pdf2image import convert_from_bytes
    POPPLER_AVAILABLE = True
except Exception:
    logger.warning("pdf2image/Poppler not available - scanned PDF OCR disabled")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF. Uses PyPDF2 for digital PDFs,
    falls back to Tesseract OCR for scanned PDFs if available."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    full_text = "\n--- PAGE BREAK ---\n".join(pages_text).strip()

    # If we got very little text, the PDF is likely scanned - try OCR
    if len(full_text) < 50:
        if TESSERACT_AVAILABLE and POPPLER_AVAILABLE:
            logger.info("PDF has little embedded text, falling back to OCR")
            return _ocr_pdf(file_bytes)
        else:
            raise ValueError(
                "PDF appears to be scanned/image-based but Tesseract and/or "
                "Poppler are not installed. Please install them for OCR support, "
                "or use a digitally-created PDF."
            )

    return full_text


def _ocr_pdf(file_bytes: bytes) -> str:
    """OCR a scanned PDF using pdf2image + Tesseract."""
    from pdf2image import convert_from_bytes
    import pytesseract

    images = convert_from_bytes(file_bytes)
    pages_text = []
    for img in images:
        text = pytesseract.image_to_string(img)
        pages_text.append(text)

    return "\n--- PAGE BREAK ---\n".join(pages_text).strip()


def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from an image using Tesseract OCR."""
    if not TESSERACT_AVAILABLE:
        raise ValueError(
            "Tesseract is not installed. Cannot process image files. "
            "Please install Tesseract for image OCR support."
        )

    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image).strip()


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Dispatch to the appropriate text extraction method based on MIME type."""
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif content_type.startswith("image/"):
        return extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {content_type}")
