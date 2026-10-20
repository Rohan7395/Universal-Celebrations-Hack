"""The tools agents act through. Each one calls controls.check() first and logs an event.

Tools post their own room messages, so the dashboard shows every action as it happens.
"""

import sqlite3
import uuid
from datetime import timedelta
from typing import Any

from app.api.models import Severity
from app.db import repo
from app.engine import clock, controls, room

DAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _guard(conn: sqlite3.Connection, tenant: str, agent: str, tool: str, **ids: Any) -> None:
    controls.check(conn, tenant, tool)
    room.event(conn, tenant, agent, "tool_call", tool, ids)


def clock_time(starts_at: str) -> str:
    """'2026-10-19T15:00' -> '3 PM'; '...T15:30' -> '3:30 PM'."""
    hh, mm = (int(x) for x in starts_at[11:16].split(":"))
    suffix = "AM" if hh < 12 else "PM"
    hour = hh % 12 or 12
    return f"{hour}:{mm:02d} {suffix}" if mm else f"{hour} {suffix}"


def first_name(name: str | None) -> str:
    return (name or "").split(" ")[0]


# ---------------------------------------------------------------- Guardian (Ben)


def open_case(
    conn: sqlite3.Connection,
    tenant: str,
    *,
    client: dict | None,
    severity: Severity,
    summary: str,
    flag_id: int | None,
) -> int:
    _guard(conn, tenant, "ben", "open_case", flag_id=flag_id, severity=severity.value)
    cur = conn.execute(
        """INSERT INTO cases (tenant_id, client_id, kind, severity, flag_id, summary)
           VALUES (?, ?, 'escalation', ?, ?, ?)""",
        (tenant, client["id"] if client else None, severity.value, flag_id, summary),
    )
    case_id = int(cur.lastrowid or 0)
    room.post(
        conn,
        tenant,
        "ben",
        "system",
        f"Case #{case_id} opened in the human queue: {summary}",
        {"case_id": case_id, "severity": severity.value, "type": "case_opened"},
    )
    return case_id


def page_on_call(
    conn: sqlite3.Connection,
    tenant: str,
    *,
    client: dict | None,
    severity: Severity,
    case_id: int,
) -> dict[str, Any]:
    _guard(conn, tenant, "ben", "page_on_call", case_id=case_id, severity=severity.value)
    rota = repo.get_tenant(conn, tenant)["on_call"]
    today = DAY_KEYS[clock.now().weekday()]
    person = next((p for p in rota if today in p.get("days", [])), rota[0] if rota else None)
    person = person or {"name": "the on-call coordinator", "reach_by": "phone"}
    who = client["name"] if client else "an unknown client"
    room.post(
        conn,
        tenant,
        "ben",
        "handoff",
        f"Paging {person['name']} (on call) by {person.get('reach_by', 'phone').replace('_', ' ')}:"
        f" {severity.value} for {who}, case #{case_id}.",
        {"case_id": case_id, "severity": severity.value, "on_call": person["name"]},
    )
    return person


def send_family_update(
    conn: sqlite3.Connection, tenant: str, *, client: dict, severity: Severity, text: str
) -> None:
    _guard(conn, tenant, "ben", "send_family_update", client_id=client["id"])
    to = client.get("family_name") or "the family contact"
    relation = client.get("family_relation")
    room.post(
        conn,
        tenant,
        "ben",
        "system",
        f"Family Update sent to {to}" + (f" ({relation})" if relation else "") + f": {text}",
        {
            "type": "family_update",
            "client_id": client["id"],
            "to": to,
            "relation": relation,
            "phone": client.get("family_phone"),
            "severity": severity.value,
            "text": text,
        },
    )


def notify_caregiver(conn: sqlite3.Connection, tenant: str, *, client: dict, note: str) -> None:
    _guard(conn, tenant, "ben", "notify_caregiver", client_id=client["id"])
    caregiver = client.get("primary_caregiver_name") or "the primary caregiver"
    room.post(
        conn,
        tenant,
        "ben",
        "system",
        f"Note to {caregiver} about {client['name']}: {note}",
        {"type": "caregiver_note", "client_id": client["id"], "caregiver": caregiver},
    )


# ---------------------------------------------------------------- Scheduler (Dana)


def find_slot(conn: sqlite3.Connection, tenant: str, *, client: dict) -> dict[str, Any] | None:
    """Earliest open slot left today, preferring the Client's primary Caregiver."""
    _guard(conn, tenant, "dana", "find_slot", client_id=client["id"])
    now = clock.now()
    end_of_day = (now + timedelta(days=1)).date().isoformat()
    rows = conn.execute(
        """SELECT v.id, v.caregiver_id, v.starts_at, v.ends_at, g.name AS caregiver_name
           FROM visits v JOIN caregivers g ON g.id = v.caregiver_id
           WHERE v.tenant_id = ? AND v.status = 'open' AND g.active = 1
             AND v.starts_at >= ? AND v.starts_at < ?
           ORDER BY v.starts_at""",
        (tenant, now.isoformat(timespec="minutes"), end_of_day),
    ).fetchall()
    slots = [dict(r) for r in rows]
    primary = [s for s in slots if s["caregiver_id"] == client.get("primary_caregiver_id")]
    return (primary or slots or [None])[0]


def book_visit(
    conn: sqlite3.Connection,
    tenant: str,
    *,
    visit_id: int,
    client: dict,
    case_id: int | None,
    reason: str,
) -> bool:
    """Book an open slot. Returns False if someone else took it first."""
    _guard(conn, tenant, "dana", "book_visit", visit_id=visit_id, client_id=client["id"])
    cur = conn.execute(
        """UPDATE visits SET status = 'booked', client_id = ?, case_id = ?, reason = ?,
                             type = 'urgent_visit'
           WHERE id = ? AND tenant_id = ? AND status = 'open'""",
        (client["id"], case_id, reason, visit_id, tenant),
    )
    return cur.rowcount == 1


# ---------------------------------------------------------------- Companion (Grace)


def start_checkin(conn: sqlite3.Connection, tenant: str, *, client: dict) -> str:
    """Open an outbound Check-in call. The kill switch blocks this tool."""
    _guard(conn, tenant, "grace", "start_checkin", client_id=client["id"])
    call_id = f"call-{uuid.uuid4().hex[:12]}"
    repo.ensure_call(conn, tenant, call_id, client["id"], "grace")
    room.post(
        conn,
        tenant,
        "grace",
        "say",
        f"Starting a Check-in call with {client['name']}.",
        {"type": "checkin_started", "call_id": call_id, "client_id": client["id"]},
    )
    return call_id
