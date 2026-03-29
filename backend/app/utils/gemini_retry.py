import asyncio
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 2  # seconds


async def call_gemini_with_retry(client, model, contents, config):
    """Call Gemini API with retry and exponential backoff for rate limits."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            return client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            if _is_rate_limit_error(e) and attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"Gemini rate limited, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)
            elif _is_rate_limit_error(e):
                raise RuntimeError(
                    "Rate limit exceeded. The AI service is experiencing high demand. "
                    "Please wait a moment and try again."
                ) from e
            else:
                raise


def _is_rate_limit_error(e: Exception) -> bool:
    error_str = str(e).lower()
    return "429" in error_str or "resource exhausted" in error_str or "rate" in error_str
