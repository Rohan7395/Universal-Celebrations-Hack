"""The human queue: escalated cases an On-call Human accepts and resolves."""

from typing import Literal

from fastapi import APIRouter, HTTPException

from app.api.models import Case, CaseAction
from app.config import settings
from app.db import repo
from app.db.database import db
from app.engine import room

router = APIRouter()


def _to_case(row: dict) -> Case:
    visit = None
    if row.get("visit_id"):
        visit = {
            "id": row["visit_id"],
            "starts_at": row["visit_starts_at"],
            "caregiver": row["visit_caregiver"],
        }
    return Case(
        id=row["id"],
        kind=row["kind"],
        status=row["status"],
        severity=row["severity"],
        summary=row["summary"],
        client_id=row["client_id"],
        client_name=row["client_name"],
        assigned_to=row["assigned_to"],
        visit=visit,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/cases", response_model=list[Case])
def list_cases(status: Literal["open", "accepted", "resolved", "all"] = "all") -> list[Case]:
    with db() as conn:
        rows = repo.list_cases(conn, settings.tenant_id, None if status == "all" else status)
    return [_to_case(r) for r in rows]


def _transition(case_id: int, to: str, body: CaseAction, allowed_from: set[str]) -> Case:
    tenant = settings.tenant_id
    with db() as conn:
        current = next((r for r in repo.list_cases(conn, tenant) if r["id"] == case_id), None)
        if current is None:
            raise HTTPException(404, f"No case {case_id}")
        if current["status"] not in allowed_from:
            raise HTTPException(409, f"Case {case_id} is {current['status']}")
        repo.set_case_status(conn, case_id, to, assigned_to=body.by)
        note = f" Note: {body.note}" if body.note else ""
        room.post(
            conn,
            tenant,
            "system",
            "system",
            f"Case #{case_id} {to} by {body.by}.{note}",
            {"type": f"case_{to}", "case_id": case_id, "by": body.by},
        )
        room.event(conn, tenant, body.by, f"case_{to}", None, {"case_id": case_id})
        row = next(r for r in repo.list_cases(conn, tenant) if r["id"] == case_id)
    return _to_case(row)


@router.post("/cases/{case_id}/accept", response_model=Case)
def accept(case_id: int, body: CaseAction) -> Case:
    return _transition(case_id, "accepted", body, {"open"})


@router.post("/cases/{case_id}/resolve", response_model=Case)
def resolve(case_id: int, body: CaseAction) -> Case:
    return _transition(case_id, "resolved", body, {"open", "accepted"})
