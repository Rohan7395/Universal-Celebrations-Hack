"""Create a fresh SQLite file and fill it with the BrightDays demo data. All data is synthetic.

The data comes from content/brightdays/clients.json. Its dates are written for 2026-10-19;
the seed shifts them so that date becomes today.

Run: uv run python -m app.db.seed [--db PATH]
"""

import argparse
import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import ROOT, settings
from app.db.database import connect, init_schema

SEED_FILE = ROOT / "content" / "brightdays" / "clients.json"
SEED_BASE_DATE = date(2026, 10, 19)
SLOT_MINUTES = 60


def _at(day: date, hhmm: str) -> datetime:
    return datetime.combine(day, datetime.strptime(hhmm, "%H:%M").time())


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="minutes")


def seed(conn: sqlite3.Connection, today: date | None = None, data: dict | None = None) -> None:
    today = today or date.today()
    data = data or json.loads(SEED_FILE.read_text())
    shift = today - SEED_BASE_DATE
    tenant: dict[str, Any] = data["tenant"]
    tid = tenant["id"]

    conn.execute(
        """INSERT INTO tenants (id, name, kind, timezone, office_phone, on_call)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            tid,
            tenant["name"],
            "home-care",
            tenant.get("timezone"),
            tenant.get("office_phone"),
            json.dumps(data.get("on_call", [])),
        ),
    )
    conn.executemany(
        "INSERT INTO caregivers (id, tenant_id, name, phone, area) VALUES (?, ?, ?, ?, ?)",
        [(c["id"], tid, c["name"], c.get("phone"), c.get("area")) for c in data["caregivers"]],
    )
    for c in data["clients"]:
        # The schema keeps one Family Contact per Client: the first one listed.
        family = (c.get("family_contacts") or [{}])[0]
        conn.execute(
            """INSERT INTO clients (id, tenant_id, name, age, phone, city, checkin_time,
                                    primary_caregiver_id, notes, family_name, family_relation,
                                    family_phone, family_prefers)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                c["id"],
                tid,
                c["name"],
                c.get("age"),
                c.get("phone"),
                c.get("city"),
                c.get("checkin_time"),
                c.get("primary_caregiver"),
                c.get("care_notes"),
                family.get("name"),
                family.get("relation"),
                family.get("phone"),
                family.get("prefers"),
            ),
        )
    for v in data.get("visits", []):
        start = _at(date.fromisoformat(v["date"]) + shift, v["start"])
        conn.execute(
            """INSERT INTO visits (tenant_id, caregiver_id, client_id, starts_at, ends_at,
                                   status, type)
               VALUES (?, ?, ?, ?, ?, 'booked', ?)""",
            (
                tid,
                v["caregiver_id"],
                v["client_id"],
                _iso(start),
                _iso(start + timedelta(hours=v["hours"])),
                v.get("type"),
            ),
        )
    # Free windows today become one-hour open slots.
    for avail in data.get("caregiver_availability_today", []):
        for window_start, window_end in avail["free"]:
            start, end = _at(today, window_start), _at(today, window_end)
            while start + timedelta(minutes=SLOT_MINUTES) <= end:
                slot_end = start + timedelta(minutes=SLOT_MINUTES)
                conn.execute(
                    """INSERT INTO visits (tenant_id, caregiver_id, starts_at, ends_at)
                       VALUES (?, ?, ?, ?)""",
                    (tid, avail["caregiver_id"], _iso(start), _iso(slot_end)),
                )
                start = slot_end
    conn.execute(
        "INSERT INTO controls (key, value, updated_by, reason) VALUES (?, ?, ?, ?)",
        (f"{tid}.outbound_checkins", "on", "seed", "default"),
    )
    conn.commit()


def create_fresh(path: Path) -> sqlite3.Connection:
    """Delete any existing file at path, then create the schema and seed it."""
    for suffix in ("", "-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    conn = connect(path)
    init_schema(conn)
    conn.execute("PRAGMA journal_mode = WAL")
    seed(conn)
    return conn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=settings.db_path)
    path = parser.parse_args().db
    conn = create_fresh(path)
    row = conn.execute(
        """SELECT (SELECT COUNT(*) FROM tenants) AS tenants,
                  (SELECT COUNT(*) FROM clients) AS clients,
                  (SELECT COUNT(*) FROM caregivers) AS caregivers,
                  (SELECT COUNT(*) FROM visits WHERE status = 'open') AS open_slots,
                  (SELECT COUNT(*) FROM visits WHERE status = 'booked') AS booked_visits"""
    ).fetchone()
    counts = dict(row)
    conn.close()
    print(f"Seeded {path}: {counts}")


if __name__ == "__main__":
    main()
