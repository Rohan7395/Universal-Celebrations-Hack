import asyncio

from app.api.stream import room_events
from app.db.database import db
from app.engine import room

WALTER = {"client_id": "walter", "what_was_said": "I felt dizzy and fell this morning"}


def test_case_accept_then_resolve(api) -> None:
    api.post("/api/flag", json=WALTER)
    [case] = api.get("/api/cases?status=open").json()
    accepted = api.post(f"/api/cases/{case['id']}/accept", json={"by": "Priya"}).json()
    assert (accepted["status"], accepted["assigned_to"]) == ("accepted", "Priya")
    resolved = api.post(
        f"/api/cases/{case['id']}/resolve", json={"by": "Priya", "note": "Rosa visited."}
    ).json()
    assert resolved["status"] == "resolved"
    assert api.post(f"/api/cases/{case['id']}/accept", json={"by": "Priya"}).status_code == 409
    assert api.post("/api/cases/999/accept", json={"by": "Priya"}).status_code == 404


def test_kill_switch_blocks_checkin_but_not_flag(api) -> None:
    assert api.post("/api/checkins", json={"client_id": "walter"}).status_code == 200

    paused = api.post(
        "/api/controls", json={"key": "outbound_checkins", "value": "paused", "by": "Priya"}
    )
    assert paused.json()["value"] == "paused"
    blocked = api.post("/api/checkins", json={"client_id": "walter"})
    assert blocked.status_code == 423

    assert api.post("/api/flag", json=WALTER).json()["severity"] == "Urgent"


def test_loosening_needs_reason(api) -> None:
    api.post("/api/controls", json={"key": "outbound_checkins", "value": "paused", "by": "Priya"})
    bad = api.post("/api/controls", json={"key": "outbound_checkins", "value": "on", "by": "Priya"})
    assert bad.status_code == 400
    ok = api.post(
        "/api/controls",
        json={
            "key": "brightdays.outbound_checkins",
            "value": "on",
            "by": "Priya",
            "reason": "Line fixed",
        },
    )
    assert ok.json()["value"] == "on"
    assert [c["value"] for c in api.get("/api/controls").json()] == ["on"]


def test_checkin_returns_call_for_grace(api) -> None:
    body = api.post("/api/checkins", json={"client_id": "walter"}).json()
    assert body["client_name"] == "Walter Brooks" and body["call_id"].startswith("call-")
    assert api.post("/api/checkins", json={"client_id": "nobody"}).status_code == 404


def test_stream_replays_then_sends_new_messages() -> None:
    with db() as conn:
        room.post(conn, "brightdays", "ben", "decision", "first", {"severity": "Urgent"})

    async def collect() -> list[str]:
        polls = 0

        async def disconnected() -> bool:
            nonlocal polls
            polls += 1
            if polls == 2:
                with db() as conn:
                    room.post(conn, "brightdays", "dana", "decision", "second")
            return polls > 3

        return [chunk async for chunk in room_events("brightdays", None, disconnected, 0)]

    chunks = asyncio.run(collect())
    data = [c for c in chunks if c.startswith("id:")]
    assert len(data) == 2
    assert '"text":"first"' in data[0] and "event: room" in data[0]
    assert '"text":"second"' in data[1]


def test_stream_resumes_after_last_event_id() -> None:
    with db() as conn:
        first = room.post(conn, "brightdays", "ben", "say", "old")
        room.post(conn, "brightdays", "ben", "say", "new")

    async def collect() -> list[str]:
        polls = 0

        async def disconnected() -> bool:
            nonlocal polls
            polls += 1
            return polls > 1

        return [c async for c in room_events("brightdays", first.id, disconnected, 0)]

    data = [c for c in asyncio.run(collect()) if c.startswith("id:")]
    assert len(data) == 1 and '"text":"new"' in data[0]
