"""POST /api/flag: Grace's only tool. M0 stub returns a fixed Urgent decision."""

from fastapi import APIRouter

from app.api.models import FlagRequest, FlagResponse, Severity

router = APIRouter()

STUB_RESPONSE = FlagResponse(
    severity=Severity.URGENT,
    actions=["open_case", "page_oncall", "request_visit", "send_family_update"],
    say="A caregiver will be with you at 3 PM.",
)


@router.post("/flag", response_model=FlagResponse)
def flag(request: FlagRequest) -> FlagResponse:
    # TODO(M1): Guardian sets Severity, Scheduler books, 5 s budget with background completion.
    return STUB_RESPONSE
