"""The agent room: `messages` rows the dashboard reads over SSE, plus structured `events`."""

import json
import sqlite3
from typing import Any

from app.api.models import RoomKind, RoomMessage
from app.db.database import utc_now


def post(
    conn: sqlite3.Connection,
    tenant: str,
    agent: str,
    kind: RoomKind,
    text: str,
    payload: dict[str, Any] | None = None,
) -> RoomMessage:
    msg = RoomMessage(tenant=tenant, agent=agent, kind=kind, text=text, payload=payload or {})
    msg.ts = utc_now()
    cur = conn.execute(
        """INSERT INTO messages (tenant_id, agent, kind, text, payload, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tenant, agent, kind, text, json.dumps(msg.payload), msg.ts),
    )
    msg.id = cur.lastrowid
    conn.commit()  # visible to the SSE poller at once
    return msg


def fetch_after(
    conn: sqlite3.Connection, tenant: str, after_id: int, limit: int = 200
) -> list[RoomMessage]:
    rows = conn.execute(
        """SELECT * FROM messages WHERE tenant_id = ? AND id > ? ORDER BY id LIMIT ?""",
        (tenant, after_id, limit),
    ).fetchall()
    return [_to_message(r) for r in rows]


def recent(conn: sqlite3.Connection, tenant: str, limit: int = 50) -> list[RoomMessage]:
    rows = conn.execute(
        """SELECT * FROM (SELECT * FROM messages WHERE tenant_id = ? ORDER BY id DESC LIMIT ?)
           ORDER BY id""",
        (tenant, limit),
    ).fetchall()
    return [_to_message(r) for r in rows]


def event(
    conn: sqlite3.Connection,
    tenant: str,
    agent: str,
    kind: str,
    tool: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Record a structured event. Pass ids and labels only, never raw client text."""
    conn.execute(
        """INSERT INTO events (tenant_id, agent, kind, tool, payload, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tenant, agent, kind, tool, json.dumps(payload or {}), utc_now()),
    )


def _to_message(row: sqlite3.Row) -> RoomMessage:
    return RoomMessage(
        id=row["id"],
        tenant=row["tenant_id"],
        agent=row["agent"],
        kind=row["kind"],
        text=row["text"],
        payload=json.loads(row["payload"]),
        ts=row["created_at"],
    )
