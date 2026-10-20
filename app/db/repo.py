"""Small read/write helpers shared by tools and the API."""

import json
import sqlite3
from typing import Any

from app.db.database import utc_now


def get_client(conn: sqlite3.Connection, tenant: str, client_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """SELECT c.*, g.name AS primary_caregiver_name
           FROM clients c LEFT JOIN caregivers g ON g.id = c.primary_caregiver_id
           WHERE c.tenant_id = ? AND c.id = ?""",
        (tenant, client_id),
    ).fetchone()
    return dict(row) if row else None


def get_tenant(conn: sqlite3.Connection, tenant: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant,)).fetchone()
    data = dict(row)
    data["on_call"] = json.loads(data["on_call"])
    return data


def ensure_call(
    conn: sqlite3.Connection, tenant: str, call_id: str, client_id: str | None, agent: str
) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO calls (id, tenant_id, client_id, direction, channel, agent)
           VALUES (?, ?, ?, 'outbound', 'voice', ?)""",
        (call_id, tenant, client_id, agent),
    )


def insert_flag(conn: sqlite3.Connection, **fields: Any) -> int:
    cols = ", ".join(fields)
    marks = ", ".join(f":{k}" for k in fields)
    cur = conn.execute(f"INSERT INTO flags ({cols}) VALUES ({marks})", fields)  # nosec B608
    return int(cur.lastrowid or 0)


def update_flag(conn: sqlite3.Connection, flag_id: int, **fields: Any) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    conn.execute(f"UPDATE flags SET {sets} WHERE id = :id", {**fields, "id": flag_id})  # nosec B608


def list_cases(
    conn: sqlite3.Connection, tenant: str, status: str | None = None
) -> list[dict[str, Any]]:
    sql = """SELECT k.*, c.name AS client_name,
                    v.id AS visit_id, v.starts_at AS visit_starts_at, g.name AS visit_caregiver
             FROM cases k
             LEFT JOIN clients c ON c.id = k.client_id
             LEFT JOIN visits v ON v.case_id = k.id AND v.status = 'booked'
             LEFT JOIN caregivers g ON g.id = v.caregiver_id
             WHERE k.tenant_id = ?"""
    params: list[Any] = [tenant]
    if status:
        sql += " AND k.status = ?"
        params.append(status)
    sql += " ORDER BY k.id DESC"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def set_case_status(
    conn: sqlite3.Connection, case_id: int, status: str, assigned_to: str | None = None
) -> None:
    conn.execute(
        """UPDATE cases SET status = ?, assigned_to = COALESCE(?, assigned_to), updated_at = ?
           WHERE id = ?""",
        (status, assigned_to, utc_now(), case_id),
    )
