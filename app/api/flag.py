"""POST /api/flag: Grace's only tool. Stub until Guardian is wired in."""

from fastapi import APIRouter

from app.api.models import Action, FlagRequest, FlagResponse, Severity

router = APIRouter()

STUB_RESPONSE = FlagResponse(
    severity=Severity.URGENT,
    actions=[Action.PAGE_ON_CALL, Action.BOOK_SAME_DAY_VISIT, Action.INFORM_FAMILY, Action.LOG],
    say="A caregiver will be with you at 3 PM.",
)


@router.post("/flag", response_model=FlagResponse)
def flag(request: FlagRequest) -> FlagResponse:
    return STUB_RESPONSE
