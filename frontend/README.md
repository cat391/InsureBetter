# InsureBetter — Frontend

React + Vite frontend for InsureBetter, a tool that helps users build evidence-based healthcare claim denial appeals.

## Tech Stack

- **React 18** with functional components and hooks
- **Vite** for dev server and bundling
- **Tailwind CSS** for utility styling
- **Playfair Display** (Google Fonts) for brand typography

## Pages & Features

### Landing Page
- Choose between two paths: **Upload Documents** or **Manual Entry**
- Radio-button style option cards with hover/selected states
- Continue button unlocks only after a selection is made

### Upload Documents Page
- **Drag-and-drop** file upload zone for EOB and denial letters
- Accepts PDF, PNG, JPG, and TIFF files (up to 25 MB each)
- Duplicate file detection — adding the same filename twice is a no-op
- Removable file chips show file type badge and truncated name
- Optional **Additional Claim Context** textarea for notes not captured in documents
- Generate Appeal button is gated behind at least one uploaded file

### Manual Entry Page
- Structured form for entering claim details: denial codes, CPT/procedure codes, ICD-10 diagnosis codes, date of service, insurance plan, and member ID
- **Reason for Denial** textarea for free-text insurer language
- **Plan & Policy Information** textarea for coverage details, prior authorizations, and physician notes
- Generate Appeal unlocks when either the plan details or denial reason field has content

### Appeal Result Page
Split-panel layout:

**Left panel — Appeal Letter**
- Formatted draft appeal letter with sender/recipient blocks, denial reference, and basis for appeal
- Expandable **Supporting Documentation** section (5 items, collapsible)
- **Download** button exports the letter as a `.txt` file
- **Text selection toolbar** — highlight selected text in yellow, sage, or rose, or click "Ask about this" to send the passage as context to the chat assistant

**Right panel — AI Chat Assistant** (sticky, stays visible while letter scrolls)
- Loads an initial appeal summary on mount (connects to `INITIAL_SUMMARY_API` when configured, falls back to a placeholder)
- Inline **typing indicator** (three bouncing dots) while responses load
- **Suggested prompts** shown after the first assistant message ("How strong is my appeal?", "What documents should I attach?", "Strengthen the medical necessity section")
- **Context chip** shows truncated selected passage when "Ask about this" is triggered; dismissible
- Textarea input with Enter-to-send and Shift+Enter for newline
- Connects to `CHAT_API_ENDPOINT` when configured; stubs a placeholder response until then

### Navigation Bar (persistent)
- Fixed top bar (48 px) with the InsureBetter logo and wordmark
- **Breadcrumb trail**: Get Started › Enter Info › Your Appeal — active step highlighted, current step bolded
- Inline disclaimer: "Not legal advice — consult a healthcare advocate for complex disputes"

### Page Transitions
- Smooth fade + slide-up animation (300 ms cubic-bezier) between all pages via a shared `PageTransition` wrapper

## Project Structure

```
src/
├── App.jsx                        # Root layout, routing state, nav bar, page transitions
└── components/
    ├── LandingPage.jsx            # Entry point — choose upload or manual path
    ├── UploadDocumentsPage.jsx    # Drag-and-drop document upload
    ├── ManualEntryPage.jsx        # Structured manual claim entry form
    └── AppealResultPage.jsx       # Generated appeal letter + AI chat assistant
```

## Getting Started

```bash
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` by default.

## API Integration Points

The appeal result page has three stub constants at the top of `AppealResultPage.jsx` that can be pointed at a backend:

| Constant | Purpose |
|---|---|
| `INITIAL_SUMMARY_API` | `POST` endpoint — receives `formData`, returns `{ summary: string }` |
| `CHAT_API_ENDPOINT` | `POST` endpoint — receives `{ messages }`, returns `{ reply: string }` |
| `APPEAL_PDF_URL` | If set, renders the letter as an `<iframe>` instead of the built-in HTML view |
