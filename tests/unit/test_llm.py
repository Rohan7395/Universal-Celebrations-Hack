import asyncio
from dataclasses import replace

import pytest
from google.genai import errors
from pydantic_ai.models.fallback import FallbackModel

from app.engine import llm


async def no_sleep(_: float) -> None:
    return None


def api_error(code: int) -> errors.APIError:
    return errors.APIError(code, {"error": {"message": "x", "status": "X"}})


def run(call, models=("big", "small")):
    return asyncio.run(llm.with_retry_and_fallback(call, models=models, sleep=no_sleep))


def test_retries_429_then_succeeds() -> None:
    seen: list[str] = []

    async def call(model: str) -> str:
        seen.append(model)
        if len(seen) < 3:
            raise api_error(429)
        return model

    assert run(call) == "big"
    assert seen == ["big", "big", "big"]


def test_falls_back_to_smaller_model_after_5xx() -> None:
    seen: list[str] = []

    async def call(model: str) -> str:
        seen.append(model)
        if model == "big":
            raise api_error(503)
        return model

    assert run(call) == "small"
    assert seen == ["big"] * llm.ATTEMPTS_PER_MODEL + ["small"]


def test_non_retryable_error_raises_immediately() -> None:
    seen: list[str] = []

    async def call(model: str) -> str:
        seen.append(model)
        raise api_error(400)

    with pytest.raises(errors.APIError):
        run(call)
    assert seen == ["big"]


def test_all_models_exhausted_raises_unavailable() -> None:
    async def call(model: str) -> str:
        raise api_error(500)

    with pytest.raises(llm.LLMUnavailable):
        run(call)


def test_backoff_is_capped() -> None:
    assert all(0 < llm.backoff_delay(n) <= llm.MAX_DELAY_S for n in range(10))


def test_agent_model_uses_pinned_ids(monkeypatch) -> None:
    monkeypatch.setattr(llm, "settings", replace(llm.settings, gemini_api_key="test-key"))
    model = llm.agent_model()
    assert isinstance(model, FallbackModel)
    names = [m.model_name for m in model.models]
    assert names == [llm.settings.gemini_model, llm.settings.gemini_fallback_model]


def test_fast_agent_model_tries_fast_model_first(monkeypatch) -> None:
    monkeypatch.setattr(llm, "settings", replace(llm.settings, gemini_api_key="test-key"))
    names = [m.model_name for m in llm.fast_agent_model().models]
    assert names == [llm.settings.gemini_fast_model, llm.settings.gemini_model]
