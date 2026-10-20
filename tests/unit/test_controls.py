import pytest

from app.engine import controls

T = "brightdays"


def test_seeded_default_is_on(conn) -> None:
    assert controls.get(conn, T, "outbound_checkins").value == "on"


def test_agent_may_tighten(conn) -> None:
    c = controls.set_value(conn, T, "outbound_checkins", "paused", by="ben", human=False)
    assert (c.value, c.updated_by) == ("paused", "ben")


def test_agent_may_not_loosen(conn) -> None:
    controls.set_value(conn, T, "outbound_checkins", "paused", by="ben", human=False)
    with pytest.raises(controls.ControlError, match="Only a human"):
        controls.set_value(conn, T, "outbound_checkins", "on", by="ben", human=False, reason="x")


def test_human_loosen_needs_a_reason(conn) -> None:
    controls.set_value(conn, T, "outbound_checkins", "paused", by="ben", human=False)
    with pytest.raises(controls.ControlError, match="reason"):
        controls.set_value(conn, T, "outbound_checkins", "on", by="Priya", human=True, reason=" ")
    c = controls.set_value(
        conn, T, "outbound_checkins", "on", by="Priya", human=True, reason="Checked the line"
    )
    assert (c.value, c.reason) == ("on", "Checked the line")


def test_changes_are_logged(conn) -> None:
    controls.set_value(conn, T, "outbound_checkins", "paused", by="Priya", human=True)
    event = conn.execute("SELECT * FROM events WHERE kind = 'control_tightened'").fetchone()
    assert event["agent"] == "Priya"
    msg = conn.execute("SELECT text FROM messages ORDER BY id DESC").fetchone()
    assert "outbound_checkins tightened" in msg["text"]


def test_check_blocks_outbound_tool_when_paused(conn) -> None:
    controls.check(conn, T, "start_checkin")  # on: passes
    controls.set_value(conn, T, "outbound_checkins", "paused", by="Priya", human=True)
    with pytest.raises(controls.ToolBlocked):
        controls.check(conn, T, "start_checkin")
    assert conn.execute("SELECT COUNT(*) FROM events WHERE kind = 'tool_blocked'").fetchone()[0]


def test_safety_tools_are_never_blocked(conn) -> None:
    controls.set_value(conn, T, "outbound_checkins", "paused", by="Priya", human=True)
    for tool in ("open_case", "page_on_call", "send_family_update", "find_slot", "book_visit"):
        controls.check(conn, T, tool)


def test_unknown_values_are_rejected(conn) -> None:
    with pytest.raises(controls.ControlError):
        controls.set_value(conn, T, "outbound_checkins", "maybe", by="Priya", human=True)
    with pytest.raises(controls.ControlError):
        controls.set_value(conn, T, "nope", "on", by="Priya", human=True)
