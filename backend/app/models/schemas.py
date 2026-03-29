from enum import Enum
from pydantic import BaseModel, Field


class DenialType(str, Enum):
    PRIOR_AUTH = "prior_authorization"
    OUT_OF_NETWORK = "out_of_network"
    MEDICAL_NECESSITY = "medical_necessity"
    CODING_ERROR = "coding_error"
    TIMELY_FILING = "timely_filing"
    EXPERIMENTAL = "experimental"
    COVERAGE_ELIGIBILITY = "coverage_eligibility"


class DenialExtractionResult(BaseModel):
    carc_code: str | None = None
    rarc_code: str | None = None
    denied_cpt_codes: list[str] = Field(default_factory=list)
    same_date_procedures: list[str] = Field(default_factory=list)
    denial_reason: str = ""
    denial_type: str | None = None
    plan_type: str | None = None
    patient_name: str | None = None
    patient_id: str | None = None
    provider_name: str | None = None
    provider_npi: str | None = None
    insurance_company: str | None = None
    claim_number: str | None = None
    date_of_service: str | None = None
    date_of_denial: str | None = None
    insurer_address: str | None = None
    appeal_deadline: str | None = None
    confidence: str = "low"
    raw_text: str = ""


class RegulationEntry(BaseModel):
    citation: str
    summary: str
    title: str = ""
    relevance: str = ""


class RegulatoryLookupResult(BaseModel):
    carc_definition: str | None = None
    rarc_definition: str | None = None
    applicable_regulations: list[RegulationEntry] = Field(default_factory=list)
    appeal_grounds: list[str] = Field(default_factory=list)
    template_language: str | None = None
    denial_type_matched: str | None = None
    appeal_deadline: str | None = None
    appeal_process: list[str] = Field(default_factory=list)
    appeal_strategy: str | None = None
    required_evidence: list[str] = Field(default_factory=list)
    escalation: str | None = None


class AppealLetterResponse(BaseModel):
    letter_text: str
    citations_used: list[str] = Field(default_factory=list)
    confidence_note: str | None = None
    denial_type: str | None = None


class FullPipelineResponse(BaseModel):
    extraction: DenialExtractionResult
    lookup: RegulatoryLookupResult
    appeal_letter: AppealLetterResponse
    processing_time_seconds: float


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    stage: str | None = None


class HealthResponse(BaseModel):
    status: str
    gemini_connected: bool
    data_files_loaded: bool


class ChatMessage(BaseModel):
    role: str
    content: str


class GenerateRequest(BaseModel):
    extraction: DenialExtractionResult
    track: str = "aca"


class ChatRequest(BaseModel):
    user_message: str
    current_letter_text: str = ""
    extraction: DenialExtractionResult
    lookup: RegulatoryLookupResult
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    additional_context: str = ""


class ChatResponse(BaseModel):
    intent: str  # "question", "edit", or "both"
    assistant_message: str
    proposed_letter: AppealLetterResponse | None = None
    proposed_extraction: DenialExtractionResult | None = None
    additional_context: str = ""
    conversation_history: list[ChatMessage]


class ManualEntryRequest(BaseModel):
    denial_codes: str = ""
    cpt_codes: str = ""
    icd10_codes: str = ""
    date_of_service: str = ""
    plan_info: str = ""
    member_id: str = ""
    denial_reason: str = ""
    plan_details: str = ""
