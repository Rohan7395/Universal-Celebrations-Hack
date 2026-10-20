"""Kill switch. Code, not prompts: every tool calls check() before it acts.

Each control has values ordered from loosest to tightest. Anyone may tighten at once.
Loosening needs a human and a reason (ADR 0003, PR-13). Every change is logged.
"""

import sqlite3

from app.api.models import Control
from app.db.database import utc_now
from app.engine import room

# Control name -> allowed values, loosest first.
LEVELS: dict[str, tuple[str, ...]] = {
    "outbound_checkins": ("on", "paused"),
}

# Tool -> the control that gates it. Tools not listed are never blocked:
# flag() and the Guardian's safety response must keep working when outbound calls are paused.
TOOL_CONTROLS: dict[str, tuple[str, str]] = {
    "start_checkin": ("outbound_checkins", "paused"),
}


class ToolBlocked(Exception):
    def __init__(self, tool: str, control: Control):
        self.tool = tool
        self.control = control
        super().__init__(f"{tool} is blocked: {control.key} is {control.value} ({control.reason})")


class ControlError(ValueError):
    pass


def _key(tenant: str, name: str) -> str:
    return f"{tenant}.{name}"


def get(conn: sqlite3.Connection, tenant: str, name: str) -> Control:
    row = conn.execute("SELECT * FROM controls WHERE key = ?", (_key(tenant, name),)).fetchone()
    if row is None:
        return Control(key=_key(tenant, name), value=LEVELS[name][0], updated_by="default")
    return Control(**dict(row))


def list_all(conn: sqlite3.Connection, tenant: str) -> list[Control]:
    return [get(conn, tenant, name) for name in LEVELS]


def check(conn: sqlite3.Connection, tenant: str, tool: str) -> None:
    """Raise ToolBlocked if a control stops this tool. Call at the top of every tool."""
    gate = TOOL_CONTROLS.get(tool)
    if gate is None:
        return
    name, blocking_value = gate
    control = get(conn, tenant, name)
    if LEVELS[name].index(control.value) >= LEVELS[name].index(blocking_value):
        room.event(conn, tenant, "system", "tool_blocked", tool, {"control": control.key})
        raise ToolBlocked(tool, control)


def set_value(
    conn: sqlite3.Connection,
    tenant: str,
    name: str,
    value: str,
    *,
    by: str,
    human: bool,
    reason: str | None = None,
) -> Control:
    """Change a control. Tightening is always allowed; loosening needs human=True and a reason."""
    if name not in LEVELS:
        raise ControlError(f"Unknown control: {name}")
    levels = LEVELS[name]
    if value not in levels:
        raise ControlError(f"{name} must be one of {levels}")
    current = get(conn, tenant, name)
    loosening = levels.index(value) < levels.index(current.value)
    reason = (reason or "").strip() or None
    if loosening and not human:
        raise ControlError(f"Only a human can loosen {name}")
    if loosening and not reason:
        raise ControlError(f"Loosening {name} needs a reason")

    control = Control(
        key=_key(tenant, name), value=value, updated_by=by, reason=reason, updated_at=utc_now()
    )
    conn.execute(
        """INSERT INTO controls (key, value, updated_by, reason, updated_at)
           VALUES (:key, :value, :updated_by, :reason, :updated_at)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value,
               updated_by = excluded.updated_by, reason = excluded.reason,
               updated_at = excluded.updated_at""",
        control.model_dump(),
    )
    changed = value != current.value
    direction = "loosened" if loosening else "tightened" if changed else "confirmed"
    room.event(
        conn,
        tenant,
        by,
        f"control_{direction}",
        None,
        {"key": control.key, "from": current.value, "to": value, "human": human},
    )
    because = f" Reason: {reason}" if reason else ""
    room.post(
        conn,
        tenant,
        "system",
        "system",
        f"Control {name} {direction}: {current.value} → {value} by {by}.{because}",
        {"control": control.model_dump()},
    )
    return control
