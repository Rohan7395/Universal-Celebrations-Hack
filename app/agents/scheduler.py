"""Dana, the Scheduler. Books same-day Caregiver visits.

Slot choice is a code rule (primary Caregiver first, then the earliest slot left today), so a
booking never waits on an LLM inside Grace's 5 s budget.
"""

import sqlite3
from typing import Any

from app.engine import room, tools


def book_same_day_visit(
    conn: sqlite3.Connection, tenant: str, *, client: dict, case_id: int | None, reason: str
) -> dict[str, Any] | None:
    """Find and book a visit for today. Returns the booked slot, or None if nothing is free."""
    for _ in range(3):  # retry if another booking takes the slot between find and book
        slot = tools.find_slot(conn, tenant, client=client)
        if slot is None:
            break
        if tools.book_visit(
            conn, tenant, visit_id=slot["id"], client=client, case_id=case_id, reason=reason
        ):
            usual = slot["caregiver_id"] == client.get("primary_caregiver_id")
            caregiver = tools.first_name(slot["caregiver_name"])
            room.post(
                conn,
                tenant,
                "dana",
                "decision",
                f"Booked {caregiver} for {client['name']} at {tools.clock_time(slot['starts_at'])}"
                " today."
                + (
                    f" {caregiver} is {tools.first_name(client['name'])}'s usual caregiver."
                    if usual
                    else ""
                ),
                {
                    "type": "visit_booked",
                    "visit_id": slot["id"],
                    "case_id": case_id,
                    "starts_at": slot["starts_at"],
                    "caregiver": slot["caregiver_name"],
                },
            )
            return slot
    room.post(
        conn,
        tenant,
        "dana",
        "decision",
        f"No open slot left today for {client['name']}. The on-call coordinator will arrange one.",
        {"type": "no_slot", "case_id": case_id},
    )
    return None
