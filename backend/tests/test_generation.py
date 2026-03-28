import pytest
from unittest.mock import MagicMock, patch

from app.models.schemas import (
    AppealLetterResponse,
    DenialExtractionResult,
    RegulationEntry,
    RegulatoryLookupResult,
)
from tests.conftest import SAMPLE_APPEAL_LETTER, SAMPLE_EXTRACTION_JSON, SAMPLE_DENIAL_TEXT


def _make_mock_client(response_text: str):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


class TestGenerateAppealLetter:
    @pytest.mark.asyncio
    async def test_produces_appeal_letter(self, sample_extraction_result, sample_lookup_result, mock_gemini_generation):
        from app.services.generation import generate_appeal_letter
        result = await generate_appeal_letter(sample_extraction_result, sample_lookup_result)
        assert isinstance(result, AppealLetterResponse)
        assert len(result.letter_text) > 100

    @pytest.mark.asyncio
    async def test_citations_extracted_from_letter(self, sample_extraction_result, sample_lookup_result, mock_gemini_generation):
        from app.services.generation import generate_appeal_letter
        result = await generate_appeal_letter(sample_extraction_result, sample_lookup_result)
        # The sample letter includes "42 USC 300gg-19" which is in lookup
        assert "42 USC 300gg-19" in result.citations_used

    @pytest.mark.asyncio
    async def test_confidence_note_when_low_confidence(self, sample_lookup_result, mock_gemini_generation):
        low_conf_extraction = DenialExtractionResult(
            **{**SAMPLE_EXTRACTION_JSON, "confidence": 0.5},
            raw_text=SAMPLE_DENIAL_TEXT,
        )
        from app.services.generation import generate_appeal_letter
        result = await generate_appeal_letter(low_conf_extraction, sample_lookup_result)
        assert result.confidence_note is not None
        assert "50%" in result.confidence_note

    @pytest.mark.asyncio
    async def test_no_confidence_note_when_high(self, sample_extraction_result, sample_lookup_result, mock_gemini_generation):
        from app.services.generation import generate_appeal_letter
        result = await generate_appeal_letter(sample_extraction_result, sample_lookup_result)
        assert result.confidence_note is None

    @pytest.mark.asyncio
    async def test_empty_lookup_still_produces_letter(self, sample_extraction_result):
        empty_lookup = RegulatoryLookupResult()
        mock_client = _make_mock_client(
            "Dear Sir, I am appealing this denial. Sincerely, Patient."
        )
        with patch("app.services.generation._get_client", return_value=mock_client):
            from app.services.generation import generate_appeal_letter
            result = await generate_appeal_letter(sample_extraction_result, empty_lookup)
            assert isinstance(result, AppealLetterResponse)
            assert len(result.letter_text) > 0
            assert result.citations_used == []

    @pytest.mark.asyncio
    async def test_gemini_failure_raises(self, sample_extraction_result, sample_lookup_result):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Rate limited")
        with patch("app.services.generation._get_client", return_value=mock_client):
            from app.services.generation import generate_appeal_letter
            with pytest.raises(RuntimeError, match="LLM generation failed"):
                await generate_appeal_letter(sample_extraction_result, sample_lookup_result)
