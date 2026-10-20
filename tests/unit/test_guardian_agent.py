import asyncio

from pydantic_ai.models.test import TestModel

from app.agents import guardian
from app.api.models import Severity


def test_review_agent_returns_structured_review() -> None:
    model = TestModel(custom_output_args={"severity": "Urgent", "reason": "Dizzy and fell."})
    result = asyncio.run(guardian.review_agent().run("I fell", model=model))
    assert result.output.severity is Severity.URGENT


def test_llm_review_fails_safe_to_none(monkeypatch) -> None:
    def boom():
        raise RuntimeError("no key")

    monkeypatch.setattr(guardian.llm, "fast_agent_model", boom)
    assert asyncio.run(guardian.llm_review("I fell", None)) is None
