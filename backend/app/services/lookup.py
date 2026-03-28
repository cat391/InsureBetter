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

# Load JSON data files at module init. Gracefully handle empty/missing files.
def _load_json(relative_path: str) -> dict:
    path = DATA_DIR / relative_path
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load {path}: {e}")
        return {}


_denial_codes = _load_json("carc_rarc/denial_codes.json")
_regulations = _load_json("regulations/aca_regulations.json")
_appeal_grounds = _load_json("appeal_grounds/grounds_by_denial_type.json")
_templates = _load_json("templates/appeal_templates.json")


def reload_data() -> None:
    """Reload all JSON data files. Useful after Person 1 updates the data."""
    global _denial_codes, _regulations, _appeal_grounds, _templates
    _denial_codes = _load_json("carc_rarc/denial_codes.json")
    _regulations = _load_json("regulations/aca_regulations.json")
    _appeal_grounds = _load_json("appeal_grounds/grounds_by_denial_type.json")
    _templates = _load_json("templates/appeal_templates.json")


def data_files_loaded() -> bool:
    """Check if any data file has actual content (not just empty {})."""
    return any(
        bool(d) for d in [_denial_codes, _regulations, _appeal_grounds, _templates]
    )


def lookup_denial_codes(
    carc_code: str | None, rarc_code: str | None
) -> tuple[str | None, str | None]:
    """Look up CARC and RARC code definitions."""
    carc_def = None
    rarc_def = None

    if carc_code:
        carc_data = _denial_codes.get("CARC", {})
        entry = carc_data.get(carc_code, {})
        carc_def = entry.get("description")

    if rarc_code:
        rarc_data = _denial_codes.get("RARC", {})
        entry = rarc_data.get(rarc_code, {})
        rarc_def = entry.get("description")

    return carc_def, rarc_def


def lookup_regulations(denial_type: str | None) -> list[RegulationEntry]:
    """Look up ACA regulations applicable to a denial type."""
    if not denial_type:
        return []

    entries = _regulations.get(denial_type, [])
    if not isinstance(entries, list):
        return []

    result = []
    for entry in entries:
        if isinstance(entry, dict):
            try:
                result.append(RegulationEntry(**entry))
            except Exception:
                logger.warning(f"Skipping malformed regulation entry: {entry}")
    return result


def lookup_appeal_grounds(denial_type: str | None) -> list[str]:
    """Look up common appeal grounds for a denial type."""
    if not denial_type:
        return []

    grounds = _appeal_grounds.get(denial_type, [])
    if not isinstance(grounds, list):
        return []
    return [g for g in grounds if isinstance(g, str)]


def lookup_template(denial_type: str | None) -> str | None:
    """Look up and assemble the appeal letter template for a denial type."""
    if not denial_type:
        return None

    template = _templates.get(denial_type, {})
    if not isinstance(template, dict):
        return None

    parts = []
    for section in ("opening", "body", "closing"):
        text = template.get(section, "")
        if text:
            parts.append(text)

    return "\n\n".join(parts) if parts else None


def perform_full_lookup(extraction: DenialExtractionResult) -> RegulatoryLookupResult:
    """Orchestrate all lookups based on extraction results."""
    carc_def, rarc_def = lookup_denial_codes(extraction.carc_code, extraction.rarc_code)
    regulations = lookup_regulations(extraction.denial_type)
    grounds = lookup_appeal_grounds(extraction.denial_type)
    template = lookup_template(extraction.denial_type)

    return RegulatoryLookupResult(
        carc_definition=carc_def,
        rarc_definition=rarc_def,
        applicable_regulations=regulations,
        appeal_grounds=grounds,
        template_language=template,
        denial_type_matched=extraction.denial_type,
    )
