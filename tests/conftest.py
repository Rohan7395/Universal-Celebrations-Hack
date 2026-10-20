"""Shared fixtures. Every test gets a fresh seeded SQLite file and a pinned clock (10:05)."""

from dataclasses import replace

import pytest

from app.db import database
from app.db.seed import create_fresh
from app.engine import clock


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
