import io

import pytest
from PyPDF2 import PdfWriter


def _create_simple_pdf() -> bytes:
    """Create a minimal PDF for upload testing."""
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=letter)
        c.drawString(72, 750, "This is a test denial letter for upload testing.")
        c.save()
        return buf.getvalue()
    except ImportError:
        # Fallback: PyPDF2 blank page (won't have extractable text though)
        buf = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.write(buf)
        return buf.getvalue()


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        # Patch the health check's Gemini call too
        from unittest.mock import patch, MagicMock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_model.generate_content.return_value = mock_response

        with patch("app.routers.appeal.genai.GenerativeModel", return_value=mock_model):
            response = client.get("/api/appeal/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "gemini_connected" in data
        assert "data_files_loaded" in data


class TestUploadEndpoint:
    def test_valid_pdf_returns_pipeline_response(self, client):
        pdf_bytes = _create_simple_pdf()
        response = client.post(
            "/api/appeal/upload",
            files={"file": ("denial.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "extraction" in data
        assert "lookup" in data
        assert "appeal_letter" in data
        assert "processing_time_seconds" in data

    def test_unsupported_file_type_returns_400(self, client):
        response = client.post(
            "/api/appeal/upload",
            files={"file": ("file.zip", b"fake zip data", "application/zip")},
        )
        assert response.status_code == 400

    def test_oversized_file_returns_413(self, client):
        # Create 11MB of data
        big_data = b"x" * (11 * 1024 * 1024)
        response = client.post(
            "/api/appeal/upload",
            files={"file": ("big.pdf", big_data, "application/pdf")},
        )
        assert response.status_code == 413


class TestExtractOnlyEndpoint:
    def test_extract_only_returns_extraction(self, client):
        pdf_bytes = _create_simple_pdf()
        response = client.post(
            "/api/appeal/extract-only",
            files={"file": ("denial.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "carc_code" in data
        assert "denial_type" in data
        assert "confidence" in data


class TestCORS:
    def test_cors_headers_present(self, client):
        response = client.options(
            "/api/appeal/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should return allow-origin header
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


class TestRootEndpoint:
    def test_root_returns_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "InsureBetter" in response.json()["message"]
