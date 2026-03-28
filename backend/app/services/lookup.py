import json
import logging
import os
from pathlib import Path

from app.models.schemas import (
    DenialExtractionResult,
    RegulationEntry,
    RegulatoryLookupResult,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "../data"))


def _load_json(filename: str):
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load {path}: {e}")
        return None


# Load data files at module init
_denial_database_raw: list = _load_json("denial_database.json") or []
_carc_lookup: dict = _load_json("carc_lookup.json") or {}
_state_contacts: dict = _load_json("state_medicaid_contacts.json") or {}

# Build a dict keyed by category_id for fast lookups
_denial_database: dict = {}
for _entry in _denial_database_raw:
    if isinstance(_entry, dict) and "category_id" in _entry:
        _denial_database[_entry["category_id"]] = _entry


def reload_data() -> None:
    """Reload all data files. Useful after data updates."""
    global _denial_database_raw, _carc_lookup, _state_contacts, _denial_database
    _denial_database_raw = _load_json("denial_database.json") or []
    _carc_lookup = _load_json("carc_lookup.json") or {}
    _state_contacts = _load_json("state_medicaid_contacts.json") or {}
    _denial_database = {}
    for entry in _denial_database_raw:
        if isinstance(entry, dict) and "category_id" in entry:
            _denial_database[entry["category_id"]] = entry


def data_files_loaded() -> bool:
    """Check if data files have actual content."""
    return bool(_denial_database) or bool(_carc_lookup)


def _normalize_carc_code(code: str) -> str:
    """Strip group code prefix (CO-, PR-, OA-, PI-) from CARC codes.
    EOBs show codes like 'CO-50' but our lookup keys are just '50'."""
    import re
    match = re.match(r'^[A-Z]{1,2}-?(\d+)$', code.strip())
    return match.group(1) if match else code


def lookup_carc_category(carc_code: str | None) -> str | None:
    """Look up which denial category a CARC code belongs to."""
    if not carc_code:
        return None
    normalized = _normalize_carc_code(carc_code)
    return _carc_lookup.get(normalized)


def lookup_denial_codes(
    carc_code: str | None, rarc_code: str | None
) -> tuple[str | None, str | None]:
    """Look up CARC code description from the denial database.
    Returns (carc_definition, rarc_definition). RARC not in current data."""
    carc_def = None
    rarc_def = None

    if carc_code:
        normalized = _normalize_carc_code(carc_code)
        category_id = _carc_lookup.get(normalized)
        if category_id and category_id in _denial_database:
            entry = _denial_database[category_id]
            carc_def = entry.get("description")

    return carc_def, rarc_def


def lookup_regulations(denial_type: str | None, track: str = "aca") -> list[RegulationEntry]:
    """Look up regulations for a denial type from a specific track."""
    if not denial_type or denial_type not in _denial_database:
        return []

    entry = _denial_database[denial_type]
    track_data = entry.get("tracks", {}).get(track, {})
    raw_regs = track_data.get("regulations", [])

    result = []
    for reg in raw_regs:
        if isinstance(reg, dict):
            try:
                result.append(RegulationEntry(
                    citation=reg.get("citation", ""),
                    summary=reg.get("summary", ""),
                ))
            except Exception:
                logger.warning(f"Skipping malformed regulation entry: {reg}")
    return result


def lookup_appeal_grounds(denial_type: str | None) -> list[str]:
    """Look up appeal grounds for a denial type."""
    if not denial_type or denial_type not in _denial_database:
        return []

    common_grounds = _denial_database[denial_type].get("common_grounds", "")
    if not common_grounds:
        return []

    return [common_grounds]


def lookup_appeal_deadline(denial_type: str | None, track: str = "aca") -> str | None:
    """Look up appeal deadline for a denial type."""
    if not denial_type or denial_type not in _denial_database:
        return None
    return _denial_database[denial_type].get("tracks", {}).get(track, {}).get("appeal_deadline")


def lookup_appeal_process(denial_type: str | None, track: str = "aca") -> list[str]:
    """Look up appeal process steps."""
    if not denial_type or denial_type not in _denial_database:
        return []
    return _denial_database[denial_type].get("tracks", {}).get(track, {}).get("appeal_process", [])


def lookup_appeal_strategy(denial_type: str | None, track: str = "aca") -> str | None:
    """Look up appeal strategy."""
    if not denial_type or denial_type not in _denial_database:
        return None
    return _denial_database[denial_type].get("tracks", {}).get(track, {}).get("appeal_strategy")


def lookup_required_evidence(denial_type: str | None, track: str = "aca") -> list[str]:
    """Look up required evidence for an appeal."""
    if not denial_type or denial_type not in _denial_database:
        return []
    return _denial_database[denial_type].get("tracks", {}).get(track, {}).get("required_evidence", [])


def lookup_escalation(denial_type: str | None, track: str = "aca") -> str | None:
    """Look up escalation path."""
    if not denial_type or denial_type not in _denial_database:
        return None
    return _denial_database[denial_type].get("tracks", {}).get(track, {}).get("escalation")


def lookup_template(denial_type: str | None, track: str = "aca") -> str | None:
    """Build template guidance from appeal_strategy + appeal_process + required_evidence."""
    if not denial_type or denial_type not in _denial_database:
        return None

    strategy = lookup_appeal_strategy(denial_type, track)
    process = lookup_appeal_process(denial_type, track)
    evidence = lookup_required_evidence(denial_type, track)

    parts = []
    if strategy:
        parts.append(f"APPEAL STRATEGY:\n{strategy}")
    if process:
        steps = "\n".join(f"  {i}. {s}" for i, s in enumerate(process, 1))
        parts.append(f"APPEAL PROCESS:\n{steps}")
    if evidence:
        items = "\n".join(f"  - {e}" for e in evidence)
        parts.append(f"REQUIRED EVIDENCE:\n{items}")

    return "\n\n".join(parts) if parts else None


def lookup_state_contacts(state_abbrev: str | None) -> dict | None:
    """Look up Medicaid contact info for a state."""
    if not state_abbrev:
        return None
    return _state_contacts.get(state_abbrev.upper())


def perform_full_lookup(extraction: DenialExtractionResult, track: str = "aca") -> RegulatoryLookupResult:
    """Orchestrate all lookups based on extraction results."""
    carc_def, rarc_def = lookup_denial_codes(extraction.carc_code, extraction.rarc_code)
    regulations = lookup_regulations(extraction.denial_type, track)
    grounds = lookup_appeal_grounds(extraction.denial_type)
    template = lookup_template(extraction.denial_type, track)

    return RegulatoryLookupResult(
        carc_definition=carc_def,
        rarc_definition=rarc_def,
        applicable_regulations=regulations,
        appeal_grounds=grounds,
        template_language=template,
        denial_type_matched=extraction.denial_type,
        appeal_deadline=lookup_appeal_deadline(extraction.denial_type, track),
        appeal_process=lookup_appeal_process(extraction.denial_type, track),
        appeal_strategy=lookup_appeal_strategy(extraction.denial_type, track),
        required_evidence=lookup_required_evidence(extraction.denial_type, track),
        escalation=lookup_escalation(extraction.denial_type, track),
    )
