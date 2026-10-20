from datetime import date

from app.db import database
from app.db.database import SCHEMA_VERSION, TABLES, connect, init_schema
from app.db.seed import create_fresh, seed


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
    assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION


def test_schema_is_idempotent() -> None:
    conn = connect(":memory:")
    init_schema(conn)
    init_schema(conn)
    assert table_names(conn) == set(TABLES)


def test_seed_loads_brightdays_content() -> None:
    conn = connect(":memory:")
    init_schema(conn)
    seed(conn, today=date(2026, 11, 2))

    walter = conn.execute("SELECT * FROM clients WHERE id = 'walter'").fetchone()
    assert walter["name"] == "Walter Brooks"
    assert (walter["family_name"], walter["family_relation"]) == ("Linda Brooks", "daughter")
    assert walter["primary_caregiver_id"] == "cg-rosa"
    assert conn.execute("SELECT COUNT(*) FROM caregivers").fetchone()[0] == 3

    # Dates shift so the content's 2026-10-19 becomes "today".
    booked = conn.execute(
        "SELECT starts_at FROM visits WHERE client_id = 'walter' AND status = 'booked'"
    ).fetchall()
    assert "2026-11-02T16:00" in {r["starts_at"] for r in booked}
    rosa_open = conn.execute(
        "SELECT starts_at FROM visits WHERE caregiver_id = 'cg-rosa' AND status = 'open'"
    ).fetchall()
    assert [r["starts_at"] for r in rosa_open] == ["2026-11-02T15:00"]


def test_create_fresh_replaces_existing_file(tmp_path) -> None:
    path = tmp_path / "care.sqlite"
    create_fresh(path).close()
    conn = create_fresh(path)  # would hit UNIQUE errors if the old file survived
    assert conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0] == 1


def test_ensure_db_recreates_a_stale_schema(tmp_path, monkeypatch) -> None:
    path = tmp_path / "old.sqlite"
    old = connect(path)
    old.execute("CREATE TABLE tenants (id TEXT)")
    old.commit()
    old.close()
    monkeypatch.setattr(database, "_db_path", path)
    database.ensure_db()
    with database.db() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 6
