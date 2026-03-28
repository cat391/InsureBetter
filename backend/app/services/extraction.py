import json
import logging
import os
import re

import google.generativeai as genai

from app.models.schemas import DenialExtractionResult

logger = logging.getLogger(__name__)

# Initialize Gemini client once at module level
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.0-flash")

EXTRACTION_PROMPT = """You are an insurance denial letter analyst. Extract structured information from the following denial letter text.

Return a JSON object with exactly these fields:
- carc_code: the CARC (Claim Adjustment Reason Code) if present, or null
- rarc_code: the RARC (Remittance Advice Remark Code) if present, or null
- cpt_codes: array of CPT/HCPCS procedure codes mentioned, or empty array
- denial_reason: the stated reason for denial, quoted from the letter
- denial_type: classify as exactly one of: "prior_authorization", "out_of_network", "medical_necessity", "coding_billing_error", "timely_filing", "experimental_investigational", or null if unclear
- plan_type: insurance plan type (HMO, PPO, ACA Marketplace, Employer-sponsored, etc.) or null
- patient_name: or null
- patient_id: member/subscriber ID or null
- provider_name: or null
- provider_npi: NPI number or null
- insurance_company: payer name or null
- claim_number: or null
- date_of_service: in YYYY-MM-DD format or null
- date_of_denial: in YYYY-MM-DD format or null
- appeal_deadline: appeal deadline date or description (e.g. "180 days from denial") or null
- confidence: float 0.0-1.0, how confident you are in this extraction overall

Return ONLY valid JSON, no markdown fences, no explanation.

DENIAL LETTER TEXT:
{raw_text}"""


def _sanitize_json_response(text: str) -> str:
    """Strip markdown fences that Gemini sometimes adds despite JSON mode."""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def extract_denial_info(raw_text: str) -> DenialExtractionResult:
    """Stage 1: Use Gemini to extract structured fields from denial letter text."""
    prompt = EXTRACTION_PROMPT.format(raw_text=raw_text)

    try:
        response = _model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
    except Exception as e:
        logger.error(f"Gemini extraction call failed: {e}")
        raise RuntimeError(f"LLM extraction failed: {e}") from e

    response_text = _sanitize_json_response(response.text)

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {response_text[:200]}")
        raise RuntimeError(f"LLM returned invalid JSON: {e}") from e

    # Build the result, using .get() for safety
    confidence = float(data.get("confidence", 0.0))
    denial_type = data.get("denial_type")

    # Low confidence: force denial_type to None so downstream adds caveats
    if confidence < 0.5:
        denial_type = None

    return DenialExtractionResult(
        carc_code=data.get("carc_code"),
        rarc_code=data.get("rarc_code"),
        cpt_codes=data.get("cpt_codes", []),
        denial_reason=data.get("denial_reason", ""),
        denial_type=denial_type,
        plan_type=data.get("plan_type"),
        patient_name=data.get("patient_name"),
        patient_id=data.get("patient_id"),
        provider_name=data.get("provider_name"),
        provider_npi=data.get("provider_npi"),
        insurance_company=data.get("insurance_company"),
        claim_number=data.get("claim_number"),
        date_of_service=data.get("date_of_service"),
        date_of_denial=data.get("date_of_denial"),
        appeal_deadline=data.get("appeal_deadline"),
        confidence=confidence,
        raw_text=raw_text,
    )
