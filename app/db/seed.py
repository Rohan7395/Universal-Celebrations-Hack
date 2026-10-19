"""Create a fresh SQLite file and fill it with the BrightDays demo data. All data is synthetic.

Run: uv run python -m app.db.seed [--db PATH]
"""

import argparse
import json
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

from app.config import settings
from app.db.database import connect, init_schema

TENANT_ID = "brightdays"
CLIENT_ID = "walter"
# (caregiver_id, start hour) for today's open one-hour slots. 15:00 is the demo's "3 PM".
OPEN_SLOTS = [
    ("cg-priya", 10),
    ("cg-marcus", 11),
    ("cg-priya", 13),
    ("cg-marcus", 15),
    ("cg-priya", 15),
    ("cg-marcus", 17),
]


def seed(conn: sqlite3.Connection, today: date | None = None) -> None:
    today = today or date.today()
    conn.execute(
        "INSERT INTO tenants (id, name, kind) VALUES (?, ?, ?)",
        (TENANT_ID, "BrightDays Home Care (synthetic demo)", "home-care"),
    )
    conn.execute(
        """INSERT INTO clients (id, tenant_id, name, phone, address, notes,
                                family_name, family_relation, family_phone, family_email)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            CLIENT_ID,
            TENANT_ID,
            "Walter Hughes",
            "+1-555-0100",
            "12 Maple Lane, Springfield",
            "84. Lives alone. Daily check-in call at 10 AM. Takes blood pressure medication.",
            "Ellen Hughes",
            "daughter",
            "+1-555-0142",
            "ellen.hughes@example.com",
        ),
    )
    conn.executemany(
        "INSERT INTO caregivers (id, tenant_id, name, phone, skills) VALUES (?, ?, ?, ?, ?)",
        [
            ("cg-priya", TENANT_ID, "Priya Nair", "+1-555-0111",
             json.dumps(["personal care", "medication support"])),
            ("cg-marcus", TENANT_ID, "Marcus Bell", "+1-555-0122",
             json.dumps(["companionship", "mobility support"])),
        ],
    )
    conn.executemany(
        "INSERT INTO visits (tenant_id, caregiver_id, starts_at, ends_at) VALUES (?, ?, ?, ?)",
        [
            (
                TENANT_ID,
                caregiver_id,
                (start := datetime.combine(today, time(hour))).isoformat(timespec="minutes"),
                (start + timedelta(hours=1)).isoformat(timespec="minutes"),
            )
            for caregiver_id, hour in OPEN_SLOTS
        ],
    )
    conn.execute(
        "INSERT INTO controls (key, value, updated_by, reason) VALUES (?, ?, ?, ?)",
        (f"{TENANT_ID}.outbound_checkins", "on", "seed", "default"),
    )
    conn.commit()


def create_fresh(path: Path) -> sqlite3.Connection:
    """Delete any existing file at path, then create the schema and seed it."""
    path.unlink(missing_ok=True)
    conn = connect(path)
    init_schema(conn)
    seed(conn)
    return conn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=settings.db_path)
    path = parser.parse_args().db
    conn = create_fresh(path)
    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # nosec B608 (fixed table names)
        for t in ("tenants", "clients", "caregivers", "visits")
    }
    conn.close()
    print(f"Seeded {path}: {counts}")


if __name__ == "__main__":
    main()
