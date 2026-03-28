import json

import pytest
from unittest.mock import MagicMock, patch

from app.models.schemas import DenialExtractionResult
from tests.conftest import SAMPLE_EXTRACTION_JSON


def _make_mock_response(text: str):
    mock = MagicMock()
    mock.text = text
    return mock


class TestExtractDenialInfo:
    @pytest.mark.asyncio
    async def test_parses_valid_json(self, mock_gemini_extraction):
        from app.services.extraction import extract_denial_info
        result = await extract_denial_info("test denial letter text")
        assert isinstance(result, DenialExtractionResult)
        assert result.carc_code == "197"
        assert result.denial_type == "prior_authorization"
        assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_strips_markdown_fences(self):
        fenced_json = f"```json\n{json.dumps(SAMPLE_EXTRACTION_JSON)}\n```"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = _make_mock_response(fenced_json)

        with patch("app.services.extraction._model", mock_model):
            from app.services.extraction import extract_denial_info
            result = await extract_denial_info("test text")
            assert result.carc_code == "197"

    @pytest.mark.asyncio
    async def test_low_confidence_forces_null_denial_type(self):
        low_conf = {**SAMPLE_EXTRACTION_JSON, "confidence": 0.3}
        mock_model = MagicMock()
        mock_model.generate_content.return_value = _make_mock_response(json.dumps(low_conf))

        with patch("app.services.extraction._model", mock_model):
            from app.services.extraction import extract_denial_info
            result = await extract_denial_info("test text")
            assert result.denial_type is None
            assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_malformed_json_raises_runtime_error(self):
        mock_model = MagicMock()
        mock_model.generate_content.return_value = _make_mock_response("not valid json at all")

        with patch("app.services.extraction._model", mock_model):
            from app.services.extraction import extract_denial_info
            with pytest.raises(RuntimeError, match="invalid JSON"):
                await extract_denial_info("test text")

    @pytest.mark.asyncio
    async def test_gemini_api_error_raises_runtime_error(self):
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API quota exceeded")

        with patch("app.services.extraction._model", mock_model):
            from app.services.extraction import extract_denial_info
            with pytest.raises(RuntimeError, match="LLM extraction failed"):
                await extract_denial_info("test text")
