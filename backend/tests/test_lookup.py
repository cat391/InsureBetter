import pytest
from unittest.mock import patch

from app.models.schemas import DenialExtractionResult, RegulationEntry
from tests.conftest import (
    TEST_DENIAL_CODES,
    TEST_REGULATIONS,
    TEST_APPEAL_GROUNDS,
    TEST_TEMPLATES,
)


def _patch_lookup_data(denial_codes=None, regulations=None, grounds=None, templates=None):
    """Patch the module-level data dicts in lookup.py."""
    return (
        patch("app.services.lookup._denial_codes", denial_codes or {}),
        patch("app.services.lookup._regulations", regulations or {}),
        patch("app.services.lookup._appeal_grounds", grounds or {}),
        patch("app.services.lookup._templates", templates or {}),
    )


class TestLookupDenialCodes:
    def test_known_carc_code(self):
        p1, p2, p3, p4 = _patch_lookup_data(denial_codes=TEST_DENIAL_CODES)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes("197", "N56")
            assert "Precertification" in carc_def
            assert "prior authorization" in rarc_def

    def test_unknown_code_returns_none(self):
        p1, p2, p3, p4 = _patch_lookup_data(denial_codes=TEST_DENIAL_CODES)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes("999", "ZZZ")
            assert carc_def is None
            assert rarc_def is None

    def test_none_inputs(self):
        p1, p2, p3, p4 = _patch_lookup_data(denial_codes=TEST_DENIAL_CODES)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes(None, None)
            assert carc_def is None
            assert rarc_def is None

    def test_empty_data_returns_none(self):
        p1, p2, p3, p4 = _patch_lookup_data()
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes("197", "N56")
            assert carc_def is None
            assert rarc_def is None


class TestLookupRegulations:
    def test_known_denial_type(self):
        p1, p2, p3, p4 = _patch_lookup_data(regulations=TEST_REGULATIONS)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_regulations
            regs = lookup_regulations("prior_authorization")
            assert len(regs) == 1
            assert isinstance(regs[0], RegulationEntry)
            assert "438.210" in regs[0].citation

    def test_unknown_type_returns_empty(self):
        p1, p2, p3, p4 = _patch_lookup_data(regulations=TEST_REGULATIONS)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_regulations
            assert lookup_regulations("unknown_type") == []

    def test_none_type_returns_empty(self):
        p1, p2, p3, p4 = _patch_lookup_data(regulations=TEST_REGULATIONS)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_regulations
            assert lookup_regulations(None) == []


class TestLookupAppealGrounds:
    def test_known_denial_type(self):
        p1, p2, p3, p4 = _patch_lookup_data(grounds=TEST_APPEAL_GROUNDS)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_appeal_grounds
            grounds = lookup_appeal_grounds("prior_authorization")
            assert len(grounds) == 2
            assert "retroactive authorization" in grounds[0]

    def test_empty_data_returns_empty(self):
        p1, p2, p3, p4 = _patch_lookup_data()
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_appeal_grounds
            assert lookup_appeal_grounds("prior_authorization") == []


class TestLookupTemplate:
    def test_known_type_concatenates_sections(self):
        p1, p2, p3, p4 = _patch_lookup_data(templates=TEST_TEMPLATES)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_template
            template = lookup_template("prior_authorization")
            assert template is not None
            assert "formally appeal" in template
            assert "respectfully request" in template

    def test_none_type_returns_none(self):
        p1, p2, p3, p4 = _patch_lookup_data(templates=TEST_TEMPLATES)
        with p1, p2, p3, p4:
            from app.services.lookup import lookup_template
            assert lookup_template(None) is None


class TestPerformFullLookup:
    def test_orchestrates_all_lookups(self):
        p1, p2, p3, p4 = _patch_lookup_data(
            denial_codes=TEST_DENIAL_CODES,
            regulations=TEST_REGULATIONS,
            grounds=TEST_APPEAL_GROUNDS,
            templates=TEST_TEMPLATES,
        )
        with p1, p2, p3, p4:
            from app.services.lookup import perform_full_lookup
            extraction = DenialExtractionResult(
                carc_code="197",
                rarc_code="N56",
                denial_type="prior_authorization",
                raw_text="test",
            )
            result = perform_full_lookup(extraction)
            assert result.carc_definition is not None
            assert result.rarc_definition is not None
            assert len(result.applicable_regulations) == 1
            assert len(result.appeal_grounds) == 2
            assert result.template_language is not None
            assert result.denial_type_matched == "prior_authorization"

    def test_empty_data_returns_empty_results(self):
        p1, p2, p3, p4 = _patch_lookup_data()
        with p1, p2, p3, p4:
            from app.services.lookup import perform_full_lookup
            extraction = DenialExtractionResult(
                carc_code="197",
                denial_type="prior_authorization",
                raw_text="test",
            )
            result = perform_full_lookup(extraction)
            assert result.carc_definition is None
            assert result.applicable_regulations == []
            assert result.appeal_grounds == []
