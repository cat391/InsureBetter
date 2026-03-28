import json

import pytest
from unittest.mock import MagicMock, patch

from app.models.schemas import DenialExtractionResult
from tests.conftest import SAMPLE_EXTRACTION_JSON


def _make_mock_client(response_text: str):
    """Create a mock genai.Client with models.generate_content returning given text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


def _make_mock_client_error(error: Exception):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = error
    return mock_client


class TestExtractDenialInfo:
    @pytest.mark.asyncio
    async def test_parses_valid_json(self, mock_gemini_extraction):
        from app.services.extraction import extract_denial_info
        result = await extract_denial_info("test denial letter text")
        assert isinstance(result, DenialExtractionResult)
        assert result.carc_code == "197"
        assert result.denial_type == "prior_authorization"
        assert result.confidence == "high"

    @pytest.mark.asyncio
    async def test_strips_markdown_fences(self):
        fenced_json = f"```json\n{json.dumps(SAMPLE_EXTRACTION_JSON)}\n```"
        mock_client = _make_mock_client(fenced_json)

        with patch("app.services.extraction._get_client", return_value=mock_client):
            from app.services.extraction import extract_denial_info
            result = await extract_denial_info("test text")
            assert result.carc_code == "197"

    @pytest.mark.asyncio
    async def test_low_confidence_forces_null_denial_type(self):
        low_conf = {**SAMPLE_EXTRACTION_JSON, "confidence": 0.3}
        mock_client = _make_mock_client(json.dumps(low_conf))

        with patch("app.services.extraction._get_client", return_value=mock_client):
            from app.services.extraction import extract_denial_info
            result = await extract_denial_info("test text")
            assert result.denial_type is None
            assert result.confidence == "low"

    @pytest.mark.asyncio
    async def test_malformed_json_raises_runtime_error(self):
        mock_client = _make_mock_client("not valid json at all")

        with patch("app.services.extraction._get_client", return_value=mock_client):
            from app.services.extraction import extract_denial_info
            with pytest.raises(RuntimeError, match="invalid JSON"):
                await extract_denial_info("test text")

    @pytest.mark.asyncio
    async def test_gemini_api_error_raises_runtime_error(self):
        mock_client = _make_mock_client_error(Exception("API quota exceeded"))

        with patch("app.services.extraction._get_client", return_value=mock_client):
            from app.services.extraction import extract_denial_info
            with pytest.raises(RuntimeError, match="LLM extraction failed"):
                await extract_denial_info("test text")
