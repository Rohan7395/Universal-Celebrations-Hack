"""POST /api/checkins: start an outbound Check-in. Blocked by the kill switch."""

from fastapi import APIRouter, HTTPException

from app.api.models import CheckinRequest, CheckinResponse
from app.config import settings
from app.db import repo
from app.db.database import db
from app.engine import controls, room, tools

router = APIRouter()


@router.post("/checkins", response_model=CheckinResponse)
def start_checkin(body: CheckinRequest) -> CheckinResponse:
    tenant = settings.tenant_id
    with db() as conn:
        client = repo.get_client(conn, tenant, body.client_id)
        if client is None:
            raise HTTPException(404, f"No client {body.client_id}")
        try:
            call_id = tools.start_checkin(conn, tenant, client=client)
        except controls.ToolBlocked as exc:
            reason = f" ({exc.control.reason})" if exc.control.reason else ""
            room.post(
                conn,
                tenant,
                "grace",
                "system",
                f"Check-in with {client['name']} blocked: outbound Check-ins are paused{reason}.",
                {"type": "tool_blocked", "tool": exc.tool, "control": exc.control.key},
            )
            raise HTTPException(423, str(exc)) from exc
    return CheckinResponse(call_id=call_id, client_id=client["id"], client_name=client["name"])
