import io

import pytest
from PyPDF2 import PdfWriter
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import letter

from app.utils.ocr import extract_text, extract_text_from_pdf


def _create_test_pdf(text: str) -> bytes:
    """Create a simple PDF with text using reportlab."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)
    # Write text line by line
    y = 750
    for line in text.split("\n"):
        c.drawString(72, y, line)
        y -= 14
    c.save()
    return buf.getvalue()


def _create_empty_pdf() -> bytes:
    """Create an empty PDF with no text."""
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buf)
    return buf.getvalue()


class TestExtractTextFromPdf:
    def test_extracts_text_from_digital_pdf(self):
        pdf_bytes = _create_test_pdf("This is a test denial letter with some content here.")
        text = extract_text_from_pdf(pdf_bytes)
        assert "test denial letter" in text

    def test_empty_pdf_raises_without_tesseract(self):
        from app.utils.ocr import TESSERACT_AVAILABLE, POPPLER_AVAILABLE
        if TESSERACT_AVAILABLE and POPPLER_AVAILABLE:
            pytest.skip("Tesseract+Poppler installed, OCR fallback will run instead of raising")
        pdf_bytes = _create_empty_pdf()
        with pytest.raises(ValueError, match="scanned|image-based|Tesseract"):
            extract_text_from_pdf(pdf_bytes)

    def test_empty_pdf_falls_back_to_ocr(self):
        from app.utils.ocr import TESSERACT_AVAILABLE, POPPLER_AVAILABLE
        if not (TESSERACT_AVAILABLE and POPPLER_AVAILABLE):
            pytest.skip("Tesseract+Poppler not installed")
        pdf_bytes = _create_empty_pdf()
        # Should not raise - OCR fallback handles it (returns empty or minimal text)
        result = extract_text_from_pdf(pdf_bytes)
        assert isinstance(result, str)


class TestExtractTextDispatcher:
    def test_pdf_dispatch(self):
        pdf_bytes = _create_test_pdf("Hello from PDF")
        text = extract_text(pdf_bytes, "application/pdf")
        assert "Hello from PDF" in text

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(b"data", "application/zip")

    def test_image_without_tesseract_raises(self):
        from app.utils.ocr import TESSERACT_AVAILABLE
        if TESSERACT_AVAILABLE:
            pytest.skip("Tesseract is installed, can't test fallback")
        with pytest.raises(ValueError, match="Tesseract"):
            extract_text(b"fake image data", "image/png")
