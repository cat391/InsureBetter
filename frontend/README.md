# Frontend — React + Vite + Tailwind

The frontend provides a four-page flow: landing → upload/manual entry → appeal result with AI chat.

## Setup

```bash
npm install
npm run dev    # http://localhost:5173
```

The Vite dev server proxies `/api` requests to `http://localhost:8000` (the backend).

## Tech Stack

- **React 18** — functional components, hooks only (no class components, no Redux)
- **Vite 5** — dev server + production bundler
- **Tailwind CSS 3.4** — utility-first styling
- **react-markdown** + **remark-breaks** — renders appeal letter markdown with proper formatting
- **diff** (npm) — line-by-line diffing for chat edit proposals
- **Google Fonts** — Playfair Display (headings) + Inter (body)

## File Structure

```
frontend/
├── index.html                         # HTML entry point
├── package.json                       # Dependencies and scripts
├── vite.config.js                     # Vite config + API proxy to backend
├── tailwind.config.js                 # Tailwind theme (Playfair Display font)
├── postcss.config.js                  # PostCSS + Tailwind + Autoprefixer
├── public/
│   └── logo.png                       # InsureBetter logo
└── src/
    ├── index.jsx                      # React DOM render entry point
    ├── index.css                      # Tailwind layers + custom component styles
    ├── App.jsx                        # Root component: routing, nav bar, page transitions
    └── components/
        ├── LandingPage.jsx            # Choose upload or manual entry path
        ├── UploadDocumentsPage.jsx    # Drag-and-drop file upload + context
        ├── ManualEntryPage.jsx        # Form-based denial details entry
        └── AppealResultPage.jsx       # Appeal letter + AI chat (main integration file)
```

## Pages

### LandingPage
Entry point with two radio-button cards: "Upload Documents" or "Manual Entry". Continue button gated behind selection.

### UploadDocumentsPage
Drag-and-drop upload zone accepting PDF, PNG, JPG, TIFF (up to 25MB). Duplicate detection, removable file chips. Optional "Additional Claim Context" textarea. On submit, sends files to `POST /api/appeal/upload` as multipart FormData.

### ManualEntryPage
Six structured fields (denial codes, CPT, ICD-10, date of service, plan info, member ID) plus denial reason and plan details textareas. On submit, sends to `POST /api/appeal/manual` as JSON.

### AppealResultPage
This is the core integration file (~500 lines). Split-panel layout:

**Left panel — Appeal Letter:**
- **Read mode** (default): Rendered markdown via `ReactMarkdown` with `remark-breaks`. Full text selection + highlighting works across paragraphs.
- **Edit mode** (toggle button): Raw markdown textarea for direct editing (address, phone, typos).
- **Diff view**: When chat proposes edits, shows line-by-line diff (red = removed, green = added) with Accept/Reject buttons.
- Supporting documentation section from `lookup.required_evidence`.
- Download button exports letter as `.txt`.

**Right panel — AI Chat:**
- Initial summary built from extraction data (denial codes, type, deadline).
- Suggested quick prompts after first message.
- Text selection toolbar: highlight in yellow/sage/rose, or "Ask about this" to send passage as chat context.
- Sends to `POST /api/appeal/chat` with `current_letter_text`, `extraction`, `lookup`, and conversation history.
- Intent-aware responses: questions answered inline, edits shown as diffs for approval.

## How the Frontend Calls the Backend

| User Action | Frontend Does | Backend Endpoint |
|-------------|--------------|-----------------|
| Upload file + click Generate | `FormData` with file | `POST /api/appeal/upload` |
| Fill form + click Generate | JSON with form fields | `POST /api/appeal/manual` |
| Ask a question in chat | JSON with message + context | `POST /api/appeal/chat` |
| Request a letter edit in chat | Same as above | `POST /api/appeal/chat` (intent=edit) |

## Key Components

### `MarkdownLine`
Inline markdown parser for `**bold**` text in chat messages. Used in chat bubbles and diff view lines.

### `SelectionToolbar`
Floating toolbar rendered via `createPortal` when text is selected in read mode. Offers highlight colors and "Ask about this" button.

### `ApprovalCard`
Rendered in the chat panel when the backend proposes letter edits. Accept applies the changes, Reject discards them.

## Styling

Color palette (warm browns/tans):
- Background: `#FAF8F4`
- Primary text: `#5C4033`
- Secondary text: `#7C6553`
- Muted accent: `#C9B99A`
- Borders: `#E8DDD5`

Custom CSS classes in `index.css`: `.selection-card`, `.upload-zone`, `.btn-primary`, `.btn-secondary`, `.field-label`, `.textarea`, `.input-field`.
