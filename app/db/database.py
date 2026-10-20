"""SQLite connection and schema setup (stdlib sqlite3).

Every request or background task opens its own short-lived connection with `db()`.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
SCHEMA_VERSION = 2

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

_db_path: Path = settings.db_path


def set_db_path(path: Path) -> None:
    """Point db() at another file (tests use a temp file)."""
    global _db_path
    _db_path = path


def db_path() -> Path:
    return _db_path


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """A connection that commits on success and rolls back on error."""
    conn = connect(_db_path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_db() -> None:
    """Create and seed the database on first run, so `make dev` works before `make seed`."""
    from app.db.seed import create_fresh

    if _db_path.exists():
        with db() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version == SCHEMA_VERSION:
            return
    create_fresh(_db_path).close()
