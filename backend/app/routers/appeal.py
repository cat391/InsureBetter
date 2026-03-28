import logging
import time

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.schemas import (
    DenialExtractionResult,
    ErrorResponse,
    FullPipelineResponse,
    HealthResponse,
)
from app.services.extraction import extract_denial_info
from app.services.generation import generate_appeal_letter
from app.services.lookup import data_files_loaded, perform_full_lookup
from app.utils.ocr import extract_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/appeal", tags=["appeal"])

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
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="Extraction failed", detail=str(e), stage="extraction"
            ).model_dump(),
        )

    # Stage 2: Regulatory lookup (deterministic, won't fail)
    lookup = perform_full_lookup(extraction)

    # Stage 3: LLM generation
    try:
        appeal_letter = await generate_appeal_letter(extraction, lookup)
    except RuntimeError as e:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="Letter generation failed", detail=str(e), stage="generation"
            ).model_dump(),
        )

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


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check: verify Gemini connectivity and data file status."""
    gemini_ok = False
    try:
        import google.generativeai as genai
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            "Reply with exactly: ok",
            generation_config=genai.GenerationConfig(max_output_tokens=5),
        )
        gemini_ok = bool(response.text)
    except Exception as e:
        logger.warning(f"Gemini health check failed: {e}")

    return HealthResponse(
        status="ok",
        gemini_connected=gemini_ok,
        data_files_loaded=data_files_loaded(),
    )
