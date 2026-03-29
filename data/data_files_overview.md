# Data Files Overview

The curated legal/regulatory database that powers InsureBetter's deterministic lookup stage. These files are loaded by the backend's `lookup.py` service at startup. The LLM never generates regulations — it only uses what's in these files.

## Files

### `denial_database.json` (52KB) — Master Database

Array of 7 denial category objects. Each contains:

| Field | Type | Description |
|-------|------|-------------|
| `denial_category` | string | Human-readable name (e.g. "Prior Authorization") |
| `category_id` | string | Machine key (e.g. "prior_authorization") |
| `carc_codes` | string[] | CARC codes that map to this category |
| `description` | string | What this denial type means |
| `common_grounds` | string | General appeal grounds for this denial type |
| `tracks` | object | Per-track appeal guidance (see below) |

Each category has 4 **tracks**: `aca`, `medicare`, `erisa`, `medicaid`. Each track contains:

| Field | Type | Description |
|-------|------|-------------|
| `regulations` | array | `{citation, summary}` — legal citations with explanations |
| `appeal_deadline` | string | Time limit for filing |
| `appeal_process` | string[] | Step-by-step appeal instructions |
| `appeal_strategy` | string | Recommended approach for this denial type |
| `template_key` | string | Reference identifier for letter templates |
| `escalation` | string | What to do if internal appeal is denied |
| `required_evidence` | string[] | Documents to include with the appeal |

### `carc_lookup.json` (1.3KB) — CARC Code Mapping

Flat dictionary mapping CARC code numbers to `category_id`:

```json
{
  "197": "prior_authorization",
  "50": "medical_necessity",
  "11": "out_of_network",
  ...
}
```

44 CARC codes mapped across 7 categories. The backend's `_normalize_carc_code()` strips group code prefixes (CO-, PR-, OA-) before lookup, so "CO-50" correctly maps to "50" → "medical_necessity".

### `category_descriptions.json` (1.3KB)

Same mapping as `carc_lookup.json`. Used for prose-based denial classification when no CARC code is available.

### `state_medicaid_contacts.json` (23KB)

Dictionary mapping state abbreviations to Medicaid fair-hearing contact info:

```json
{
  "PA": {
    "state_name": "Pennsylvania",
    "agency": "PA Department of Human Services",
    "appeal_body": "Bureau of Hearings and Appeals",
    "phone": "1-800-692-7462",
    "online_portal": null,
    "mailing_address": "P.O. Box 2675, Harrisburg, PA 17105",
    "notes": "..."
  }
}
```

All 50 states + DC included. Used for state-specific appeal routing in Medicaid track letters.

### `sample_denials/`

Synthetic denial letter samples for testing. Not real PHI.

- `sample_prior_auth_denial.txt` — Prior authorization denial (CARC 197, CPT 27447)

## How the Backend Uses This Data

1. **`lookup.py`** loads all JSON files at startup into module-level dicts
2. When a CARC code is extracted, `carc_lookup.json` maps it to a `category_id`
3. The `category_id` keys into `denial_database.json` to retrieve regulations, grounds, deadlines, evidence, etc.
4. The generation prompt receives this data and uses it to write the appeal letter
5. `reload_data()` can refresh files without restarting the server

## Notes

- All JSON files are consumed directly by the backend — no preprocessing needed
- `state_medicaid_contacts.json` should be spot-checked if used beyond demo
- The data supports 4 tracks but the default pipeline uses ACA. Other tracks are available via the `track` parameter on `/api/appeal/generate`
