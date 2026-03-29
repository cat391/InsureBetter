import json
import logging
import os

from google import genai
from google.genai import types

from app.models.schemas import (
    AppealLetterResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DenialExtractionResult,
    LetterSection,
)
from app.services.generation import generate_appeal_letter, _sections_to_text
from app.services.lookup import perform_full_lookup

logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        _client = genai.Client(api_key=api_key)
    return _client


INTENT_PROMPT = """You are analyzing a user's chat message about their insurance appeal letter. Classify the intent and respond accordingly.

The user's current appeal context:
- Denial type: {denial_type}
- CARC code: {carc_code}
- Denied procedures: {denied_cpt_codes}
- Denial reason: {denial_reason}
- Patient: {patient_name}
- Insurance: {insurance_company}

Applicable regulations: {regulations}

User message: {user_message}

Classify the intent as EXACTLY one of:
- "question" — the user is asking for information or explanation
- "edit" — the user wants to change the letter
- "both" — the user asks a question AND wants a change

Return a JSON object with these fields:
- intent: "question", "edit", or "both"
- answer: if intent is "question" or "both", provide a helpful answer. If intent is "edit", set to null.
- field_updates: if intent is "edit" or "both", a JSON object of extraction fields to update. If "question", set to {{}}.
- edit_description: if intent is "edit" or "both", a brief description of what changes were requested. If "question", set to null.

Return ONLY valid JSON."""

TARGETED_EDIT_PROMPT = """You are editing an existing insurance appeal letter. The letter is stored as a JSON array of sections.

CURRENT LETTER SECTIONS:
{current_sections_json}

USER REQUEST:
{user_message}

RULES:
1. Only modify sections that directly relate to the user's request.
2. Unchanged sections MUST be returned with their text EXACTLY as-is — do not rephrase, reword, or restructure them.
3. Do NOT add, remove, or modify any regulatory citations unless explicitly asked.
4. You may add or remove sections if the user explicitly asks.
5. Do not modify the "disclaimer" section.

Return a JSON object with TWO fields:
- "sections": the complete array of sections with edits applied (unchanged sections copied exactly)
- "changes_summary": a brief explanation of what you changed and why (1-2 sentences)

Return ONLY valid JSON."""


async def process_chat_message(request: ChatRequest) -> ChatResponse:
    """Process a chat message with intent classification."""

    intent_result = await _classify_intent(request)

    intent = intent_result.get("intent", "question")
    answer = intent_result.get("answer")
    field_updates = intent_result.get("field_updates", {})
    edit_description = intent_result.get("edit_description")

    updated_history = list(request.conversation_history)
    updated_history.append(ChatMessage(role="user", content=request.user_message))

    if intent == "question":
        assistant_message = answer or "I'm not sure how to answer that. Could you rephrase?"
        updated_history.append(ChatMessage(role="assistant", content=assistant_message))

        return ChatResponse(
            intent="question",
            assistant_message=assistant_message,
            proposed_letter=None,
            proposed_extraction=None,
            additional_context=request.additional_context,
            conversation_history=updated_history,
        )

    # Intent is "edit" or "both"
    updated_extraction = _apply_field_updates(request.extraction, field_updates)

    # If denial_type changed, need full pipeline regen
    if "denial_type" in field_updates:
        lookup = perform_full_lookup(updated_extraction)
        accumulated_context = request.additional_context
        if edit_description:
            accumulated_context = f"{accumulated_context}\n{edit_description}" if accumulated_context else edit_description

        proposed_letter = await generate_appeal_letter(
            updated_extraction, lookup, additional_context=accumulated_context
        )
        changes_summary = f"Regenerated the letter with updated denial type: {field_updates['denial_type']}."
    else:
        # Targeted edit on JSON sections
        proposed_letter, changes_summary = await _targeted_edit_sections(
            request.current_letter_sections, request.user_message, field_updates
        )
        accumulated_context = request.additional_context

    # Build assistant message
    if intent == "both" and answer:
        assistant_message = f"{answer}\n\n{changes_summary}"
    else:
        assistant_message = changes_summary

    updated_history.append(ChatMessage(role="assistant", content=assistant_message))

    return ChatResponse(
        intent=intent,
        assistant_message=assistant_message,
        proposed_letter=proposed_letter,
        proposed_extraction=updated_extraction,
        additional_context=accumulated_context,
        conversation_history=updated_history,
    )


async def _targeted_edit_sections(
    current_sections: list[LetterSection], user_message: str, field_updates: dict
) -> tuple[AppealLetterResponse, str]:
    """Make targeted edits to letter sections. Returns (proposed_letter, changes_summary)."""
    sections_json = json.dumps(
        [{"type": s.type, "text": s.text} for s in current_sections],
        indent=2,
    )

    edit_instructions = user_message
    if field_updates:
        updates_str = ", ".join(f"{k}: {v}" for k, v in field_updates.items())
        edit_instructions = f"{user_message}\n\nAlso update these fields in the letter: {updates_str}"

    prompt = TARGETED_EDIT_PROMPT.format(
        current_sections_json=sections_json,
        user_message=edit_instructions,
    )

    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
    except Exception as e:
        logger.error(f"Targeted section edit failed: {e}")
        raise RuntimeError(f"Letter edit failed: {e}") from e

    raw_sections = result.get("sections", [])
    changes_summary = result.get("changes_summary", "Changes applied to your letter.")

    sections = []
    for item in raw_sections:
        if isinstance(item, dict) and "type" in item and "text" in item:
            sections.append(LetterSection(type=item["type"], text=item["text"]))

    letter_text = _sections_to_text(sections)

    return AppealLetterResponse(
        letter_sections=sections,
        letter_text=letter_text,
        citations_used=[],
        confidence_note=None,
        denial_type=None,
    ), changes_summary


async def _classify_intent(request: ChatRequest) -> dict:
    """Use LLM to classify intent and extract field updates / answer in one call."""
    regulations_summary = ", ".join(
        reg.citation for reg in request.lookup.applicable_regulations
    ) if request.lookup.applicable_regulations else "None loaded"

    prompt = INTENT_PROMPT.format(
        denial_type=request.extraction.denial_type or "Unknown",
        carc_code=request.extraction.carc_code or "None",
        denied_cpt_codes=", ".join(request.extraction.denied_cpt_codes) or "None",
        denial_reason=request.extraction.denial_reason or "None",
        patient_name=request.extraction.patient_name or "None",
        insurance_company=request.extraction.insurance_company or "None",
        regulations=regulations_summary,
        user_message=request.user_message,
    )

    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Intent classification failed: {e}")
        return {"intent": "question", "answer": "I'm having trouble processing that. Could you try rephrasing?", "field_updates": {}}


def _apply_field_updates(
    extraction: DenialExtractionResult, updates: dict
) -> DenialExtractionResult:
    """Apply field updates to a copy of the extraction result."""
    if not updates:
        return extraction

    data = extraction.model_dump()
    allowed_fields = {
        "patient_name", "patient_id", "provider_name", "provider_npi",
        "insurance_company", "insurer_address", "claim_number",
        "date_of_service", "date_of_denial", "denial_type", "plan_type",
        "denial_reason", "appeal_deadline", "carc_code", "rarc_code",
    }
    for key, value in updates.items():
        if key in allowed_fields:
            data[key] = value

    return DenialExtractionResult(**data)
