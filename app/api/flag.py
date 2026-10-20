"""POST /api/flag: Grace's only tool. Guardian decides; Grace says the `say` line."""

from fastapi import APIRouter

from app.agents import guardian
from app.api.models import FlagRequest, FlagResponse
from app.config import settings

router = APIRouter()


@router.post("/flag", response_model=FlagResponse)
async def flag(request: FlagRequest) -> FlagResponse:
    return await guardian.handle_flag(request, settings.tenant_id)
