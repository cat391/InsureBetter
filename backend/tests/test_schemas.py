import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AppealLetterResponse,
    DenialExtractionResult,
    DenialType,
    FullPipelineResponse,
    RegulationEntry,
    RegulatoryLookupResult,
)


class TestDenialType:
    def test_has_all_seven_types(self):
        assert len(DenialType) == 7

    def test_values(self):
        expected = {
            "prior_authorization",
            "out_of_network",
            "medical_necessity",
            "coding_error",
            "timely_filing",
            "experimental",
            "coverage_eligibility",
        }
        assert {t.value for t in DenialType} == expected


class TestDenialExtractionResult:
    def test_valid_full_data(self):
        result = DenialExtractionResult(
            carc_code="197",
            rarc_code="N56",
            cpt_codes=["27447"],
            denial_reason="Prior auth not obtained",
            denial_type="prior_authorization",
            confidence=0.95,
            raw_text="some text",
        )
        assert result.carc_code == "197"
        assert result.confidence == 0.95

    def test_optional_fields_default_none(self):
        result = DenialExtractionResult(raw_text="text")
        assert result.carc_code is None
        assert result.patient_name is None
        assert result.appeal_deadline is None
        assert result.cpt_codes == []
        assert result.confidence == 0.0

    def test_rejects_bad_confidence_type(self):
        with pytest.raises(ValidationError):
            DenialExtractionResult(confidence="not_a_float", raw_text="text")


class TestRegulationEntry:
    def test_with_all_fields(self):
        entry = RegulationEntry(
            citation="42 CFR 438.210(d)",
            title="Coverage and authorization",
            summary="MCOs must have authorization systems",
            relevance="Applies to prior auth denials",
        )
        assert entry.citation == "42 CFR 438.210(d)"

    def test_minimal_fields(self):
        entry = RegulationEntry(
            citation="42 USC 300gg-19",
            summary="Requires internal claims appeals.",
        )
        assert entry.citation == "42 USC 300gg-19"
        assert entry.title == ""
        assert entry.relevance == ""

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            RegulationEntry(citation="42 CFR")


class TestFullPipelineResponse:
    def test_nests_correctly(self, sample_extraction_result, sample_lookup_result):
        letter = AppealLetterResponse(letter_text="Dear Sir...", denial_type="prior_authorization")
        response = FullPipelineResponse(
            extraction=sample_extraction_result,
            lookup=sample_lookup_result,
            appeal_letter=letter,
            processing_time_seconds=5.2,
        )
        assert response.extraction.carc_code == "197"
        assert response.lookup.denial_type_matched == "prior_authorization"
        assert response.processing_time_seconds == 5.2
