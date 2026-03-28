# Data Files Overview

Purpose
This file summarizes what each data file contains so other team members (e.g., Claude) can use the data consistently.

Files and Contents
1. `data/denial_database.json`
   - Array of 7 denial categories.
   - Each entry includes `denial_category`, `category_id`, `carc_codes`, `description`, `common_grounds`.
   - Each entry has 4 tracks: `aca`, `medicare`, `erisa`, `medicaid`.
   - Each track includes `regulations`, `appeal_deadline`, `appeal_process`, `appeal_strategy`, `template_key`, `escalation`, `required_evidence`.
2. `data/carc_lookup.json`
   - Map of CARC code string to `category_id`.
   - Used for fast lookup when a code is extracted.
3. `data/category_descriptions.json`
   - Same mapping as `carc_lookup.json`.
   - Used when a denial reason is prose and needs category classification.
4. `data/state_medicaid_contacts.json`
   - Map of state abbreviation to Medicaid fair‑hearing contact info.
   - Fields: `state_name`, `agency`, `appeal_body`, `phone`, `online_portal`, `mailing_address`, `notes`.
   - Used to populate state‑specific routing info in Medicaid appeal letters.
5. `data/appeal_grounds/grounds_by_denial_type.json`
   - Plain‑English appeal grounds grouped by denial category.
   - Useful for populating “common grounds” or suggested arguments.
6. `data/carc_rarc/denial_codes.json`
   - Reference list of CARC/RARC codes and descriptions.
   - Used for validation and code description lookups.
7. `data/templates/appeal_templates.json`
   - Template text blocks keyed by template identifiers.
   - Used to generate appeal letters with the correct structure and tone.
8. `data/regulations/aca_regulations.json`
   - ACA regulation references and summaries.
   - Used to populate `regulations` fields for ACA track entries.

Notes
- JSON files are intended to be consumed directly by the backend API.
- `state_medicaid_contacts.json` should be spot‑checked if used beyond demo.
