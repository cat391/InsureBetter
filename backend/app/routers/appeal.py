import logging
import time

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.schemas import (
    AppealLetterResponse,
    ChatRequest,
    ChatResponse,
    DenialExtractionResult,
    ErrorResponse,
    FullPipelineResponse,
    GenerateRequest,
    HealthResponse,
    ManualEntryRequest,
    RegulatoryLookupResult,
)
from app.services.extraction import extract_denial_info
from app.services.generation import generate_appeal_letter
from app.services.lookup import data_files_loaded, perform_full_lookup
from app.utils.ocr import extract_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/appeal", tags=["appeal"])


def _raise_for_runtime_error(e: RuntimeError, stage: str):
    """Raise HTTPException with 429 for rate limits, 422 for other errors."""
    msg = str(e).lower()
    if "rate limit" in msg or "429" in msg:
        raise HTTPException(
            status_code=429,
            detail=ErrorResponse(
                error="Rate limit exceeded",
                detail="The AI service is experiencing high demand. Please wait a moment and try again.",
                stage=stage,
            ).model_dump(),
        )
    raise HTTPException(
        status_code=422,
        detail=ErrorResponse(
            error=f"{stage.capitalize()} failed", detail=str(e), stage=stage
        ).model_dump(),
    )

ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=FullPipelineResponse)
async def upload_and_process(file: UploadFile = File(...)):
    """Full pipeline: extract text -> LLM extraction -> lookup -> LLM generation."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Unsupported file type",
                detail=f"Got {file.content_type}. Accepted: PDF, PNG, JPEG, TIFF",
                stage="upload",
            ).model_dump(),
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=ErrorResponse(
                error="File too large",
                detail=f"Max size is {MAX_FILE_SIZE // (1024*1024)}MB",
                stage="upload",
            ).model_dump(),
        )

    start = time.perf_counter()

    # Stage 0: Text extraction (OCR)
    try:
        raw_text = extract_text(file_bytes, file.content_type)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="Text extraction failed", detail=str(e), stage="ocr"
            ).model_dump(),
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="No text could be extracted from the document",
                detail="The document appears to be empty or unreadable",
                stage="ocr",
            ).model_dump(),
        )

    # Stage 1: LLM extraction
    try:
        extraction = await extract_denial_info(raw_text)
    except RuntimeError as e:
        _raise_for_runtime_error(e, "extraction")

    # Stage 2: Regulatory lookup (deterministic, won't fail)
    lookup = perform_full_lookup(extraction)

    # Stage 3: LLM generation
    try:
        appeal_letter = await generate_appeal_letter(extraction, lookup)
    except RuntimeError as e:
        _raise_for_runtime_error(e, "generation")

    elapsed = time.perf_counter() - start

    return FullPipelineResponse(
        extraction=extraction,
        lookup=lookup,
        appeal_letter=appeal_letter,
        processing_time_seconds=round(elapsed, 2),
    )


@router.post("/extract-only", response_model=DenialExtractionResult)
async def extract_only(file: UploadFile = File(...)):
    """Debug/demo endpoint: runs only Stage 1 (extraction)."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Unsupported file type",
                detail=f"Got {file.content_type}. Accepted: PDF, PNG, JPEG, TIFF",
                stage="upload",
            ).model_dump(),
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        raw_text = extract_text(file_bytes, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        extraction = await extract_denial_info(raw_text)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return extraction


@router.post("/manual", response_model=FullPipelineResponse)
async def manual_entry(request: ManualEntryRequest):
    """Generate appeal from manually entered form fields."""
    from app.services.lookup import lookup_carc_category

    start = time.perf_counter()

    # Parse CARC code — strip any prefix like "CO-"
    carc_code = request.denial_codes.split(",")[0].strip() if request.denial_codes else None

    # Parse CPT codes
    denied_cpt_codes = [c.strip() for c in request.cpt_codes.split(",") if c.strip()]

    # Build extraction from form fields
    extraction = DenialExtractionResult(
        carc_code=carc_code,
        denied_cpt_codes=denied_cpt_codes,
        denial_reason=request.denial_reason,
        date_of_service=request.date_of_service or None,
        patient_id=request.member_id or None,
        plan_type=request.plan_info or None,
        raw_text=f"{request.denial_reason}\n{request.plan_details}",
        confidence="medium",
    )

    # Use CARC lookup to classify denial_type
    if carc_code:
        category = lookup_carc_category(carc_code)
        if category:
            extraction.denial_type = category

    # If no CARC match but we have a denial reason, use LLM to classify
    if not extraction.denial_type and request.denial_reason:
        try:
            from app.services.extraction import extract_denial_info
            llm_extraction = await extract_denial_info(
                f"Denial reason: {request.denial_reason}\nPlan details: {request.plan_details}"
            )
            extraction.denial_type = llm_extraction.denial_type
        except RuntimeError:
            pass  # Proceed without classification

    lookup = perform_full_lookup(extraction)

    try:
        appeal_letter = await generate_appeal_letter(extraction, lookup)
    except RuntimeError as e:
        _raise_for_runtime_error(e, "generation")

    elapsed = time.perf_counter() - start

    return FullPipelineResponse(
        extraction=extraction,
        lookup=lookup,
        appeal_letter=appeal_letter,
        processing_time_seconds=round(elapsed, 2),
    )


@router.post("/generate", response_model=FullPipelineResponse)
async def generate_from_extraction(request: GenerateRequest):
    """Generate/regenerate appeal letter from extraction data. Runs lookup + generation."""
    start = time.perf_counter()

    lookup = perform_full_lookup(request.extraction, track=request.track)

    try:
        appeal_letter = await generate_appeal_letter(request.extraction, lookup)
    except RuntimeError as e:
        _raise_for_runtime_error(e, "generation")

    elapsed = time.perf_counter() - start

    return FullPipelineResponse(
        extraction=request.extraction,
        lookup=lookup,
        appeal_letter=appeal_letter,
        processing_time_seconds=round(elapsed, 2),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_refine(request: ChatRequest):
    """Chat endpoint: refine appeal letter through pipeline-grounded conversation."""
    from app.services.chat import process_chat_message

    try:
        return await process_chat_message(request)
    except RuntimeError as e:
        _raise_for_runtime_error(e, "chat")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check: verify Gemini connectivity and data file status."""
    gemini_ok = False
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=__import__("os").environ.get("GEMINI_API_KEY", ""))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply with exactly: ok",
            config=types.GenerateContentConfig(max_output_tokens=5),
        )
        gemini_ok = bool(response.text)
    except Exception as e:
        logger.warning(f"Gemini health check failed: {e}")

    return HealthResponse(
        status="ok",
        gemini_connected=gemini_ok,
        data_files_loaded=data_files_loaded(),
    )
