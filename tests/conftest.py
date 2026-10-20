"""Shared fixtures. Every test gets a fresh seeded SQLite file and a pinned clock (10:05)."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.agents import guardian
from app.db import database
from app.db.seed import create_fresh
from app.engine import clock


class FakeReview:
    """Stands in for the Guardian LLM. Set .result to a GuardianReview, or leave None."""

    def __init__(self) -> None:
        self.result: guardian.GuardianReview | None = None
        self.delay = 0.0
        self.calls: list[str] = []

    async def __call__(self, text: str, client: dict | None) -> guardian.GuardianReview | None:
        import asyncio

        self.calls.append(text)
        if self.delay:
            await asyncio.sleep(self.delay)
        return self.result


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    path = tmp_path / "care.sqlite"
    create_fresh(path).close()
    monkeypatch.setattr(database, "_db_path", path)
    monkeypatch.setattr(clock, "settings", replace(clock.settings, demo_now="10:05"))
    return path


@pytest.fixture
def conn(fresh_db):
    with database.db() as c:
        yield c


@pytest.fixture
def review(monkeypatch) -> FakeReview:
    fake = FakeReview()
    monkeypatch.setattr(guardian, "llm_review", fake)
    return fake


@pytest.fixture
def api(review):
    from app.main import app

    with TestClient(app) as client:
        yield client
