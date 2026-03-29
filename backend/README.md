# Backend — FastAPI

The backend orchestrates a three-stage pipeline: extraction (LLM) → regulatory lookup (JSON database) → letter generation (LLM). It also provides a chat endpoint for iterative refinement.

## Setup

```bash
cp .env.example .env   # Add your GEMINI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`. Interactive API docs at `/docs`.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google AI Studio API key (required) | — |
| `DATA_DIR` | Path to data directory | `../data` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:5173` |
| `TESSERACT_PATH` | Path to Tesseract binary (optional, for image OCR) | System default |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/appeal/upload` | Upload a denial letter (PDF/image) → full pipeline → appeal letter |
| `POST` | `/api/appeal/manual` | Submit form fields → classify denial → generate appeal |
| `POST` | `/api/appeal/generate` | Regenerate letter from existing extraction data |
| `POST` | `/api/appeal/extract-only` | Extract fields only (debug endpoint) |
| `POST` | `/api/appeal/chat` | Chat-based refinement with intent classification |
| `GET` | `/api/appeal/health` | Check Gemini connectivity and data file status |

## File Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS config, router registration
│   ├── __init__.py
│   ├── models/
│   │   └── schemas.py        # Pydantic models — the API contract
│   ├── routers/
│   │   └── appeal.py         # All API endpoints
│   ├── services/
│   │   ├── extraction.py     # Stage 1: Gemini extracts structured fields from denial text
│   │   ├── lookup.py         # Stage 2: Deterministic JSON lookup (regulations, grounds, evidence)
│   │   ├── generation.py     # Stage 3: Gemini generates appeal letter from facts + regulations
│   │   └── chat.py           # Chat service: intent classification → question or targeted edit
│   └── utils/
│       └── ocr.py            # PDF text extraction (PyPDF2) + image OCR (Tesseract fallback)
├── tests/
│   ├── conftest.py           # Shared fixtures, mock Gemini responses
│   ├── test_api.py           # Endpoint tests (upload, generate, chat, health)
│   ├── test_extraction.py    # Extraction service tests (JSON parsing, confidence, errors)
│   ├── test_generation.py    # Generation tests (letter output, citations, confidence notes)
│   ├── test_lookup.py        # Lookup tests (CARC codes, regulations, state contacts, prefix stripping)
│   ├── test_ocr.py           # OCR tests (PDF extraction, Tesseract fallback)
│   └── test_schemas.py       # Pydantic model validation tests
├── requirements.txt
├── .env.example
└── .env                      # (gitignored) Your actual config
```

## Key Files Explained

### `services/extraction.py`
Sends denial letter text to Gemini with a structured prompt. Extracts: CARC/RARC codes, denied CPT codes, same-date procedures (for clinical complexity arguments), patient/provider info, insurer address, appeal deadline. Converts Gemini's float confidence (0-1) to string ("high"/"medium"/"low"). Low confidence forces `denial_type` to null.

### `services/lookup.py`
Pure deterministic lookups — no LLM. Loads `denial_database.json` and `carc_lookup.json` at startup. Normalizes CARC codes (strips "CO-", "PR-" prefixes). Returns: regulation citations, appeal grounds, deadlines, process steps, required evidence, escalation paths. Supports ACA/Medicare/ERISA/Medicaid tracks.

### `services/generation.py`
Builds a detailed prompt with extracted facts, regulations, clinical context, and appeal strategy. Tells the LLM to write from the patient's voice, use today's date, omit placeholders, and argue specifically against the stated denial reason. Outputs markdown-formatted text.

### `services/chat.py`
Classifies user intent in one LLM call:
- **question** → answers using extraction/lookup context, no letter change
- **edit** → targeted text edit on current letter markdown, returns `changes_summary` explaining modifications
- **both** → answers the question + proposes edits

For edits: passes the current letter text + user instruction to the LLM with strict rules ("do NOT rewrite unchanged paragraphs"). If `denial_type` changes, falls back to full pipeline regeneration.

## Testing

```bash
python -m pytest tests/ -v
```

All tests use mocked Gemini responses — no API key needed to run tests. 54 tests cover schemas, OCR, extraction, lookup, generation, chat, and API endpoints.
