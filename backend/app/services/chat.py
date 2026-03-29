import json
import logging
import os

from google import genai
from google.genai import types

from app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DenialExtractionResult,
)
from app.services.generation import generate_appeal_letter
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
- "question" — the user is asking for information or explanation (e.g. "what does this regulation mean?", "why was my claim denied?")
- "edit" — the user wants to change the letter (e.g. "make it more assertive", "change my name", "add a paragraph about the emergency")
- "both" — the user asks a question AND wants a change (e.g. "can you explain that citation and remove it?")

Return a JSON object with these fields:
- intent: "question", "edit", or "both"
- answer: if intent is "question" or "both", provide a helpful answer to their question using the appeal context and regulations. If intent is "edit", set to null.
- field_updates: if intent is "edit" or "both", a JSON object of extraction fields to update (e.g. {{"patient_name": "John Smith"}}). Only include fields that need changing. If intent is "question", set to {{}}.
- edit_description: if intent is "edit" or "both", a brief description of what letter changes were requested. If intent is "question", set to null.

Return ONLY valid JSON."""


async def process_chat_message(request: ChatRequest) -> ChatResponse:
    """Process a chat message with intent classification."""

    # Step 1: Classify intent + get answer/field_updates in one call
    intent_result = await _classify_intent(request)

    intent = intent_result.get("intent", "question")
    answer = intent_result.get("answer")
    field_updates = intent_result.get("field_updates", {})
    edit_description = intent_result.get("edit_description")

    # Build updated conversation history
    updated_history = list(request.conversation_history)
    updated_history.append(ChatMessage(role="user", content=request.user_message))

    if intent == "question":
        # Question only — answer without touching the letter
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

    # Intent is "edit" or "both" — regenerate letter through pipeline
    updated_extraction = _apply_field_updates(request.extraction, field_updates)

    # Re-run lookup if denial_type changed
    if "denial_type" in field_updates:
        lookup = perform_full_lookup(updated_extraction)
    else:
        lookup = request.lookup

    # Accumulate context for generation
    new_context = edit_description or request.user_message
    if request.additional_context:
        accumulated_context = f"{request.additional_context}\n{new_context}"
    else:
        accumulated_context = new_context

    # Re-generate letter through the pipeline
    proposed_letter = await generate_appeal_letter(
        updated_extraction, lookup, additional_context=accumulated_context
    )

    # Build assistant message
    if intent == "both" and answer:
        assistant_message = f"{answer}\n\nI've also proposed changes to your letter based on your request."
    else:
        fields_changed = ", ".join(field_updates.keys()) if field_updates else ""
        if fields_changed:
            assistant_message = f"I've proposed updates to your letter. Fields updated: {fields_changed}. {edit_description or ''}"
        else:
            assistant_message = f"I've proposed changes to your letter: {edit_description or 'adjustments based on your request'}."

    updated_history.append(ChatMessage(role="assistant", content=assistant_message))

    return ChatResponse(
        intent=intent,
        assistant_message=assistant_message,
        proposed_letter=proposed_letter,
        proposed_extraction=updated_extraction,
        additional_context=accumulated_context,
        conversation_history=updated_history,
    )


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
        # Default to question intent on failure
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
