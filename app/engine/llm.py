"""Gemini access with retry/backoff on 429/5xx and fallback to a smaller model.

Two entry points:
- `generate()` for direct google-genai calls (ingest labelling, research grounding).
- `agent_model()` for Pydantic AI agents.
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import errors, types
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.config import settings

log = logging.getLogger(__name__)

RETRYABLE_CODES = frozenset({429, 500, 502, 503, 504})
ATTEMPTS_PER_MODEL = 3
INITIAL_DELAY_S = 1.0
MAX_DELAY_S = 8.0


class LLMUnavailable(RuntimeError):
    """Both the primary and the fallback model failed with retryable errors."""


def is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, errors.APIError) and exc.code in RETRYABLE_CODES


def backoff_delay(attempt: int) -> float:
    """Exponential backoff with jitter in [cap/2, cap]. attempt is 0-based."""
    cap = min(MAX_DELAY_S, INITIAL_DELAY_S * 2**attempt)
    # Jitter only, not crypto.
    return random.uniform(cap / 2, cap)  # nosec B311


async def with_retry_and_fallback[T](
    call: Callable[[str], Awaitable[T]],
    models: tuple[str, ...] | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Run call(model) with retries per model, moving to the next model when one is exhausted.

    Non-retryable errors (bad request, auth) raise immediately: a smaller model won't fix them.
    """
    models = models or (settings.gemini_model, settings.gemini_fallback_model)
    last: BaseException | None = None
    for model in models:
        for attempt in range(ATTEMPTS_PER_MODEL):
            try:
                return await call(model)
            except Exception as exc:
                if not is_retryable(exc):
                    raise
                last = exc
                log.warning("Gemini %s attempt %d failed: %s", model, attempt + 1, exc)
                if attempt + 1 < ATTEMPTS_PER_MODEL:
                    await sleep(backoff_delay(attempt))
        log.warning("Gemini %s exhausted; falling back", model)
    raise LLMUnavailable(f"All Gemini models failed: {models}") from last


@lru_cache(maxsize=1)
def client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


async def generate(
    contents: Any, config: types.GenerateContentConfig | None = None
) -> types.GenerateContentResponse:
    """generate_content on the pinned model, with retry/backoff and fallback."""

    async def call(model: str) -> types.GenerateContentResponse:
        return await client().aio.models.generate_content(
            model=model, contents=contents, config=config
        )

    return await with_retry_and_fallback(call)


def _provider() -> GoogleProvider:
    return GoogleProvider(
        api_key=settings.gemini_api_key,
        retry_options=types.HttpRetryOptions(
            attempts=ATTEMPTS_PER_MODEL,
            initial_delay=INITIAL_DELAY_S,
            max_delay=MAX_DELAY_S,
            http_status_codes=sorted(RETRYABLE_CODES),
        ),
    )


def agent_model() -> FallbackModel:
    """Model for Pydantic AI agents: the SDK retries 429/5xx, then FallbackModel switches models."""
    provider = _provider()
    return FallbackModel(
        GoogleModel(settings.gemini_model, provider=provider),
        GoogleModel(settings.gemini_fallback_model, provider=provider),
    )


def fast_agent_model() -> FallbackModel:
    """For latency-bound checks: the fast model first, the main model if it fails."""
    provider = _provider()
    return FallbackModel(
        GoogleModel(settings.gemini_fast_model, provider=provider),
        GoogleModel(settings.gemini_model, provider=provider),
    )
