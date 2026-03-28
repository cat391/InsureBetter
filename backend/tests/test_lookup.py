import pytest
from unittest.mock import patch

from app.models.schemas import DenialExtractionResult, RegulationEntry
from tests.conftest import (
    TEST_DENIAL_DATABASE,
    TEST_CARC_LOOKUP,
    TEST_STATE_CONTACTS,
)


def _build_denial_db_dict():
    """Build the category_id-keyed dict that lookup.py uses internally."""
    return {e["category_id"]: e for e in TEST_DENIAL_DATABASE}


def _patch_lookup_data(denial_db=None, carc_lookup=None, state_contacts=None):
    """Patch the module-level data in lookup.py."""
    db = denial_db if denial_db is not None else {}
    carc = carc_lookup if carc_lookup is not None else {}
    state = state_contacts if state_contacts is not None else {}
    return (
        patch("app.services.lookup._denial_database", db),
        patch("app.services.lookup._carc_lookup", carc),
        patch("app.services.lookup._state_contacts", state),
    )


class TestLookupCarcCategory:
    def test_known_code(self):
        p1, p2, p3 = _patch_lookup_data(carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_carc_category
            assert lookup_carc_category("197") == "prior_authorization"
            assert lookup_carc_category("4") == "coding_error"

    def test_strips_group_code_prefix(self):
        p1, p2, p3 = _patch_lookup_data(carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_carc_category
            assert lookup_carc_category("CO-197") == "prior_authorization"
            assert lookup_carc_category("PR-4") == "coding_error"
            assert lookup_carc_category("OA-16") == "coding_error"

    def test_unknown_code(self):
        p1, p2, p3 = _patch_lookup_data(carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_carc_category
            assert lookup_carc_category("999") is None

    def test_none_input(self):
        p1, p2, p3 = _patch_lookup_data(carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_carc_category
            assert lookup_carc_category(None) is None


class TestLookupDenialCodes:
    def test_known_carc_code(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db, carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes("197", "N56")
            assert "prior authorization" in carc_def.lower()
            assert rarc_def is None  # RARC not in new data format

    def test_carc_with_group_prefix(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db, carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_denial_codes
            carc_def, _ = lookup_denial_codes("CO-197", None)
            assert carc_def is not None
            assert "prior authorization" in carc_def.lower()

    def test_unknown_code_returns_none(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db, carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes("999", None)
            assert carc_def is None

    def test_empty_data_returns_none(self):
        p1, p2, p3 = _patch_lookup_data()
        with p1, p2, p3:
            from app.services.lookup import lookup_denial_codes
            carc_def, rarc_def = lookup_denial_codes("197", "N56")
            assert carc_def is None
            assert rarc_def is None


class TestLookupRegulations:
    def test_known_denial_type(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_regulations
            regs = lookup_regulations("prior_authorization")
            assert len(regs) == 2
            assert isinstance(regs[0], RegulationEntry)
            assert "300gg-19" in regs[0].citation

    def test_unknown_type_returns_empty(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_regulations
            assert lookup_regulations("unknown_type") == []

    def test_none_type_returns_empty(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_regulations
            assert lookup_regulations(None) == []


class TestLookupAppealGrounds:
    def test_known_denial_type(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_appeal_grounds
            grounds = lookup_appeal_grounds("prior_authorization")
            assert len(grounds) == 1
            assert "retroactively" in grounds[0]

    def test_empty_data_returns_empty(self):
        p1, p2, p3 = _patch_lookup_data()
        with p1, p2, p3:
            from app.services.lookup import lookup_appeal_grounds
            assert lookup_appeal_grounds("prior_authorization") == []


class TestLookupAppealDeadline:
    def test_known_type(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_appeal_deadline
            deadline = lookup_appeal_deadline("prior_authorization")
            assert "180 days" in deadline

    def test_unknown_type(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_appeal_deadline
            assert lookup_appeal_deadline("unknown") is None


class TestLookupTemplate:
    def test_builds_from_strategy_and_process(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_template
            template = lookup_template("prior_authorization")
            assert template is not None
            assert "APPEAL STRATEGY" in template
            assert "APPEAL PROCESS" in template
            assert "REQUIRED EVIDENCE" in template

    def test_none_type_returns_none(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db)
        with p1, p2, p3:
            from app.services.lookup import lookup_template
            assert lookup_template(None) is None


class TestLookupStateContacts:
    def test_known_state(self):
        p1, p2, p3 = _patch_lookup_data(state_contacts=TEST_STATE_CONTACTS)
        with p1, p2, p3:
            from app.services.lookup import lookup_state_contacts
            info = lookup_state_contacts("PA")
            assert info["state_name"] == "Pennsylvania"

    def test_unknown_state(self):
        p1, p2, p3 = _patch_lookup_data(state_contacts=TEST_STATE_CONTACTS)
        with p1, p2, p3:
            from app.services.lookup import lookup_state_contacts
            assert lookup_state_contacts("XX") is None

    def test_case_insensitive(self):
        p1, p2, p3 = _patch_lookup_data(state_contacts=TEST_STATE_CONTACTS)
        with p1, p2, p3:
            from app.services.lookup import lookup_state_contacts
            assert lookup_state_contacts("pa") is not None


class TestPerformFullLookup:
    def test_orchestrates_all_lookups(self):
        db = _build_denial_db_dict()
        p1, p2, p3 = _patch_lookup_data(denial_db=db, carc_lookup=TEST_CARC_LOOKUP)
        with p1, p2, p3:
            from app.services.lookup import perform_full_lookup
            extraction = DenialExtractionResult(
                carc_code="197",
                rarc_code="N56",
                denial_type="prior_authorization",
                raw_text="test",
            )
            result = perform_full_lookup(extraction)
            assert result.carc_definition is not None
            assert len(result.applicable_regulations) == 2
            assert len(result.appeal_grounds) == 1
            assert result.template_language is not None
            assert result.denial_type_matched == "prior_authorization"
            assert result.appeal_deadline is not None
            assert len(result.appeal_process) == 4
            assert result.appeal_strategy is not None
            assert len(result.required_evidence) == 3
            assert result.escalation is not None

    def test_empty_data_returns_empty_results(self):
        p1, p2, p3 = _patch_lookup_data()
        with p1, p2, p3:
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
            assert result.appeal_deadline is None
