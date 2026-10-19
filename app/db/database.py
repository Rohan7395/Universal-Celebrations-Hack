"""SQLite connection and schema setup (stdlib sqlite3)."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

TABLES = (
    "tenants",
    "clients",
    "caregivers",
    "visits",
    "calls",
    "flags",
    "cases",
    "messages",
    "events",
    "controls",
    "proposals",
    "fleet_skills",
)


def connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
