"""Kill-switch API for the dashboard. Requests here come from a human, so they may loosen."""

from fastapi import APIRouter, HTTPException

from app.api.models import Control, ControlUpdate
from app.config import settings
from app.db.database import db
from app.engine import controls

router = APIRouter()


@router.get("/controls", response_model=list[Control])
def list_controls() -> list[Control]:
    with db() as conn:
        return controls.list_all(conn, settings.tenant_id)


@router.post("/controls", response_model=Control)
def set_control(body: ControlUpdate) -> Control:
    name = body.key.removeprefix(f"{settings.tenant_id}.")
    with db() as conn:
        try:
            return controls.set_value(
                conn,
                settings.tenant_id,
                name,
                body.value,
                by=body.by,
                human=True,
                reason=body.reason,
            )
        except controls.ControlError as exc:
            raise HTTPException(400, str(exc)) from exc
