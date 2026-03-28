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


FIELD_UPDATE_PROMPT = """You are analyzing a user's chat message about their insurance appeal letter. The user may want to:
1. Correct extracted information (e.g. "my name is actually John", "the plan is an HMO")
2. Request tone/style changes (e.g. "make it more assertive")
3. Add context (e.g. "this was an emergency surgery")

Given the user's message, determine if any extraction fields should be updated.

Current extraction fields:
- patient_name: {patient_name}
- patient_id: {patient_id}
- provider_name: {provider_name}
- provider_npi: {provider_npi}
- insurance_company: {insurance_company}
- insurer_address: {insurer_address}
- claim_number: {claim_number}
- date_of_service: {date_of_service}
- date_of_denial: {date_of_denial}
- denial_type: {denial_type}
- plan_type: {plan_type}
- denial_reason: {denial_reason}
- appeal_deadline: {appeal_deadline}

User message: {user_message}

Return a JSON object with ONLY the fields that should be updated. Return empty object {{}} if no fields need changing. Do NOT include fields that stay the same.

Return ONLY valid JSON, no explanation."""

SUMMARY_PROMPT = """The user asked to modify their insurance appeal letter. Briefly describe what changes were made (1-2 sentences).

User request: {user_message}
Fields updated: {fields_updated}
Additional context added: {additional_context_added}

Return ONLY the summary sentence(s)."""


async def process_chat_message(request: ChatRequest) -> ChatResponse:
    """Process a chat message: detect field updates, re-run pipeline, return new letter."""

    # Step 1: Detect field updates from user message
    field_updates = await _detect_field_updates(request.extraction, request.user_message)

    # Step 2: Apply field updates to extraction
    updated_extraction = _apply_field_updates(request.extraction, field_updates)

    # Step 3: Re-run lookup if denial_type changed
    if "denial_type" in field_updates:
        lookup = perform_full_lookup(updated_extraction)
    else:
        lookup = request.lookup

    # Step 4: Build additional context from this and prior messages
    new_context = request.user_message
    if request.additional_context:
        accumulated_context = f"{request.additional_context}\n{new_context}"
    else:
        accumulated_context = new_context

    # Step 5: Re-generate letter through the pipeline with additional context
    appeal_letter = await generate_appeal_letter(
        updated_extraction, lookup, additional_context=accumulated_context
    )

    # Step 6: Generate a short summary of what changed
    fields_changed = ", ".join(field_updates.keys()) if field_updates else "none"
    assistant_message = await _generate_summary(
        request.user_message, fields_changed, new_context
    )

    # Step 7: Build updated conversation history
    updated_history = list(request.conversation_history)
    updated_history.append(ChatMessage(role="user", content=request.user_message))
    updated_history.append(ChatMessage(role="assistant", content=assistant_message))

    return ChatResponse(
        appeal_letter=appeal_letter,
        assistant_message=assistant_message,
        extraction=updated_extraction,
        additional_context=accumulated_context,
        conversation_history=updated_history,
    )


async def _detect_field_updates(
    extraction: DenialExtractionResult, user_message: str
) -> dict:
    """Use LLM to detect if the user wants to update any extraction fields."""
    prompt = FIELD_UPDATE_PROMPT.format(
        patient_name=extraction.patient_name or "None",
        patient_id=extraction.patient_id or "None",
        provider_name=extraction.provider_name or "None",
        provider_npi=extraction.provider_npi or "None",
        insurance_company=extraction.insurance_company or "None",
        insurer_address=extraction.insurer_address or "None",
        claim_number=extraction.claim_number or "None",
        date_of_service=extraction.date_of_service or "None",
        date_of_denial=extraction.date_of_denial or "None",
        denial_type=extraction.denial_type or "None",
        plan_type=extraction.plan_type or "None",
        denial_reason=extraction.denial_reason or "None",
        appeal_deadline=extraction.appeal_deadline or "None",
        user_message=user_message,
    )

    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        text = response.text.strip()
        # Strip markdown fences
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Field update detection failed, proceeding without updates: {e}")
        return {}


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


async def _generate_summary(
    user_message: str, fields_updated: str, additional_context: str
) -> str:
    """Generate a brief summary of changes made."""
    prompt = SUMMARY_PROMPT.format(
        user_message=user_message,
        fields_updated=fields_updated,
        additional_context_added=additional_context,
    )

    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=100,
            ),
        )
        return response.text.strip()
    except Exception:
        return "Letter has been regenerated with your requested changes."
