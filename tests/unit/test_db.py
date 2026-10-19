from datetime import date

from app.db.database import TABLES, connect, init_schema
from app.db.seed import CLIENT_ID, create_fresh, seed


def table_names(conn) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {r["name"] for r in rows}


def test_schema_creates_all_twelve_tables() -> None:
    conn = connect(":memory:")
    init_schema(conn)
    assert table_names(conn) == set(TABLES)
    assert len(TABLES) == 12


def test_schema_is_idempotent() -> None:
    conn = connect(":memory:")
    init_schema(conn)
    init_schema(conn)
    assert table_names(conn) == set(TABLES)


def test_seed_fills_demo_data() -> None:
    conn = connect(":memory:")
    init_schema(conn)
    seed(conn, today=date(2026, 10, 19))

    walter = conn.execute("SELECT * FROM clients WHERE id = ?", (CLIENT_ID,)).fetchone()
    assert walter["name"].startswith("Walter")
    assert walter["family_relation"] == "daughter"
    assert walter["family_phone"]
    assert conn.execute("SELECT COUNT(*) FROM caregivers").fetchone()[0] == 2

    slots = conn.execute("SELECT starts_at, status FROM visits").fetchall()
    assert slots and all(s["status"] == "open" for s in slots)
    assert all(s["starts_at"].startswith("2026-10-19") for s in slots)
    assert "2026-10-19T15:00" in {s["starts_at"] for s in slots}


def test_create_fresh_replaces_existing_file(tmp_path) -> None:
    path = tmp_path / "care.sqlite"
    create_fresh(path).close()
    conn = create_fresh(path)  # would hit UNIQUE errors if the old file survived
    assert conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0] == 1
