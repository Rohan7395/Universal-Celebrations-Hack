"""POST /api/flag end to end, with the Guardian LLM mocked (see conftest.FakeReview)."""

import time

from app.agents import guardian
from app.api.models import Severity

WALTER = {"client_id": "walter", "what_was_said": "I felt dizzy and fell this morning"}


def room(api) -> list[dict]:
    return api.get("/api/messages").json()


def test_live_demo_case(api) -> None:
    body = api.post("/api/flag", json=WALTER).json()

    assert body["severity"] == "Urgent"
    assert set(body["actions"]) == {"page_on_call", "book_same_day_visit", "inform_family", "log"}
    assert "Rosa" in body["say"] and "3 PM" in body["say"]

    feed = [(m["agent"], m["kind"]) for m in room(api)]
    assert feed[0] == ("grace", "handoff")
    assert feed[1] == ("ben", "decision")
    assert ("dana", "decision") in feed
    assert feed[-1] == ("grace", "say")
    texts = " ".join(m["text"] for m in room(api))
    assert "Booked Rosa for Walter Brooks at 3 PM" in texts
    assert "Family Update sent to Linda Brooks (daughter)" in texts
    assert "Paging Priya Nair" in texts or "Paging Marcus Webb" in texts

    [case] = api.get("/api/cases?status=open").json()
    assert case["severity"] == "Urgent" and case["client_name"] == "Walter Brooks"
    assert case["visit"]["caregiver"] == "Rosa Delgado"


def test_slot_is_not_double_booked(api) -> None:
    first = api.post("/api/flag", json=WALTER).json()
    second = api.post("/api/flag", json=WALTER).json()
    assert "Rosa" in first["say"] and "3 PM" in first["say"]
    # Rosa's only slot is taken, so the earliest other slot goes next.
    assert "Amara" in second["say"] and "11 AM" in second["say"]


def test_emergency_advises_911_without_waiting_for_llm(api, review) -> None:
    body = api.post(
        "/api/flag", json={"client_id": "ruth", "what_was_said": "I'm on the floor, can't get up"}
    ).json()
    assert body["severity"] == "Emergency"
    assert "advise_911" in body["actions"]
    assert body["say"].startswith("Please call 911")
    assert review.calls == []  # nothing ranks above Emergency


def test_self_harm_gets_crisis_line(api) -> None:
    said = "Everyone would be better off if I just didn't wake up."
    body = api.post("/api/flag", json={"client_id": "margaret", "what_was_said": said}).json()
    assert body["severity"] == "Emergency"
    assert "988" in body["say"]


def test_llm_can_raise(api, review) -> None:
    review.result = guardian.GuardianReview(severity=Severity.URGENT, reason="Diabetic + shaky.")
    said = "A little shaky this morning, and sweaty."
    body = api.post("/api/flag", json={"client_id": "henry", "what_was_said": said}).json()
    assert body["severity"] == "Urgent"
    assert any("by review" in m["text"] for m in room(api))


def test_llm_cannot_lower(api, review) -> None:
    review.result = guardian.GuardianReview(severity=Severity.ROUTINE, reason="Sounds fine.")
    assert api.post("/api/flag", json=WALTER).json()["severity"] == "Urgent"


def test_unmatched_flag_without_llm_stays_cautious(api, review) -> None:
    said = "Something feels off today."
    body = api.post("/api/flag", json={"client_id": "walter", "what_was_said": said}).json()
    assert body["severity"] == "Watch"


def test_llm_routine_clears_an_unmatched_flag(api, review) -> None:
    review.result = guardian.GuardianReview(severity=Severity.ROUTINE, reason="Small talk.")
    said = "What time is Rosa coming today?"
    body = api.post("/api/flag", json={"client_id": "ruth", "what_was_said": said}).json()
    assert body == {"severity": "Routine", "actions": [], "say": body["say"]}


def test_slow_llm_answers_on_rules_then_upgrades_late(api, review, monkeypatch) -> None:
    monkeypatch.setattr(guardian, "LLM_WAIT_S", 0.05)
    review.delay = 0.3
    review.result = guardian.GuardianReview(severity=Severity.EMERGENCY, reason="Head injury.")
    body = api.post("/api/flag", json=WALTER).json()
    assert body["severity"] == "Urgent"  # answered from rules, inside the budget

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if any("Raised to Emergency" in m["text"] for m in room(api)):
            break
        time.sleep(0.05)
    texts = [m["text"] for m in room(api)]
    assert any("Raised to Emergency" in t for t in texts)
    assert sum(t.startswith("Paging") for t in texts) == 2  # paged again at the new level
    [case] = api.get("/api/cases").json()
    assert case["severity"] == "Emergency"


def test_over_budget_returns_fallback_line(api, monkeypatch) -> None:
    monkeypatch.setattr(guardian, "FLAG_BUDGET_S", 0.0)
    body = api.post("/api/flag", json=WALTER).json()
    assert body["say"] == "I've let your care team know."
    assert body["severity"] == "Urgent"


def test_unknown_client_still_escalates(api) -> None:
    said = "I fell down the stairs"
    body = api.post("/api/flag", json={"client_id": "nobody", "what_was_said": said}).json()
    assert body["severity"] == "Urgent"
    [case] = api.get("/api/cases").json()
    assert "unknown client id 'nobody'" in case["summary"]


def test_flag_rejects_missing_fields(api) -> None:
    assert api.post("/api/flag", json={"client_id": "walter"}).status_code == 422


def test_events_hold_no_raw_text(api) -> None:
    from app.db.database import db

    api.post("/api/flag", json=WALTER)
    with db() as conn:
        payloads = [r["payload"] for r in conn.execute("SELECT payload FROM events")]
    assert payloads and not any("dizzy" in p for p in payloads)
