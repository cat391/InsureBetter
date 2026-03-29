# InsureBetter

**Insurance Denial Appeal Assistant** — a web app that helps people fight health insurance claim denials by generating professional, regulation-backed appeal letters.

Over half of insurance denials are overturned on appeal. The problem isn't that appeals are hard to win — it's that people don't know *how* to appeal. InsureBetter bridges that gap.

## How It Works

The app uses a **three-stage pipeline** that keeps the AI grounded in real regulations:

1. **Extract** — Upload a denial letter (PDF/image) or enter details manually. The LLM extracts structured fields: CARC codes, CPT codes, denial reason, dates, patient/provider info.
2. **Lookup** — The extracted denial code is matched against a curated database of ACA regulations, appeal grounds, deadlines, and required evidence. This is deterministic — no LLM interpretation.
3. **Generate** — The LLM composes a formal appeal letter using *only* the extracted facts and database-sourced regulations. Every citation is verifiable.

Users can then refine the letter through an AI chat assistant that classifies intent (question vs. edit), proposes targeted changes with a diff view, and requires approval before applying.

## Architecture

```
frontend/ (React + Vite + Tailwind)
  ├── Upload or Manual Entry
  ├── Appeal Letter Display (rendered markdown, read/edit toggle)
  └── Chat Assistant (intent classification, diff-based edits)

backend/ (Python + FastAPI)
  ├── /api/appeal/upload    — Full pipeline from file upload
  ├── /api/appeal/manual    — Full pipeline from form fields
  ├── /api/appeal/generate  — Regenerate from extraction data
  ├── /api/appeal/chat      — Intent-aware chat (question/edit/both)
  └── /api/appeal/health    — Health check

data/ (Curated JSON databases)
  ├── denial_database.json       — 7 denial categories x 4 tracks (ACA/Medicare/ERISA/Medicaid)
  ├── carc_lookup.json           — CARC code → denial category mapping
  ├── state_medicaid_contacts.json — State-specific Medicaid appeal contacts
  └── sample_denials/            — Synthetic test documents
```

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, a [Google AI Studio](https://aistudio.google.com/) API key (free tier)

```bash
# 1. Backend
cd backend
cp .env.example .env          # Add your GEMINI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload  # Runs on localhost:8000

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev                    # Runs on localhost:5173
```

Visit `http://localhost:5173` and upload a denial letter or enter details manually.

## Denial Types Supported

| Category | CARC Codes | Example |
|----------|------------|---------|
| Prior Authorization | 197, 15, 27, 204, 198 | "Precertification not obtained" |
| Medical Necessity | 50, 150, 151, 54, 167, 146 | "Not deemed medically necessary" |
| Out-of-Network | 11, 22, 109, 24, 119, 5 | "Provider not in network" |
| Coding/Billing Error | 4, 16, 97, 18, 45, 6-9, 125, 181 | "Procedure code inconsistent" |
| Timely Filing | 29, 39 | "Claim submitted past deadline" |
| Experimental | 55, 56, 183, 188 | "Investigational treatment" |
| Coverage/Eligibility | 26, 96, 1-3, 31-33, 170, 186 | "Not covered under plan" |

## Key Design Decisions

- **Database-first, not LLM-first.** Regulations come from a curated JSON database, not LLM generation. The LLM's role is extraction and composition.
- **Intent classification for chat.** Questions ("what does CO-50 mean?") are answered without touching the letter. Edits trigger targeted changes with diff approval.
- **CARC code normalization.** Group code prefixes (CO-, PR-, OA-) are stripped before lookup so "CO-50" correctly maps to CARC 50.
- **Same-date procedures.** The extraction captures non-denied procedures from the same visit date, giving the LLM concrete evidence for clinical complexity arguments.

## Project Structure

See individual README files in each directory:
- [`backend/README.md`](backend/README.md) — API endpoints, services, setup
- [`frontend/README.md`](frontend/README.md) — Components, UI features, development
- [`data/data_files_overview.md`](data/data_files_overview.md) — Database schemas and content

## Team

Built at HackPSU Spring 2026.

## Disclaimer

This tool does not provide legal advice. It helps structure appeals using government-mandated processes. For complex ERISA cases, consult a healthcare advocate.
