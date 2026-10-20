"""Pydantic models for the frozen contracts in docs/BUILD-PLAN.md §4, plus the M1 API shapes."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Guardian Severity, lowest to highest. Compare with `rank`, not string order."""

    ROUTINE = "Routine"
    WATCH = "Watch"
    URGENT = "Urgent"
    EMERGENCY = "Emergency"

    @property
    def rank(self) -> int:
        return list(Severity).index(self)

    @classmethod
    def highest(cls, *levels: "Severity | None") -> "Severity":
        return max((s for s in levels if s is not None), key=lambda s: s.rank, default=cls.ROUTINE)


class Action(StrEnum):
    """The response vocabulary shared with content/safety/scenarios.json."""

    ADVISE_911 = "advise_911"
    PAGE_ON_CALL = "page_on_call"
    BOOK_SAME_DAY_VISIT = "book_same_day_visit"
    INFORM_FAMILY = "inform_family"
    NOTIFY_CAREGIVER = "notify_caregiver"
    DEFLECT_MEDICAL_ADVICE = "deflect_medical_advice"
    LOG = "log"


class FlagRequest(BaseModel):
    """What Grace's `flag` client tool sends. ElevenLabs may not supply a call_id."""

    client_id: str = Field(min_length=1, max_length=100)
    what_was_said: str = Field(min_length=1, max_length=4000)
    call_id: str | None = Field(default=None, max_length=100)


class FlagResponse(BaseModel):
    severity: Severity
    actions: list[Action] = Field(default_factory=list)
    say: str


RoomKind = Literal["say", "handoff", "decision", "system"]


class RoomMessage(BaseModel):
    """A line in the agent room. Stored in `messages` and pushed over SSE."""

    tenant: str
    agent: str
    kind: RoomKind
    text: str
    payload: dict[str, Any] = Field(default_factory=dict)
    id: int | None = None
    ts: str | None = None


class Event(BaseModel):
    """A structured audit event. Never holds raw client text."""

    tenant: str
    agent: str
    kind: str
    tool: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class Control(BaseModel):
    """A kill-switch row. Agents may only tighten; loosening needs a human and a reason."""

    key: str
    value: str
    updated_by: str
    reason: str | None = None
    updated_at: str | None = None


class ControlUpdate(BaseModel):
    """A human change from the dashboard's kill-switch panel."""

    key: str
    value: str
    by: str = Field(min_length=1)
    reason: str | None = None


class SkillFrontmatter(BaseModel):
    """The YAML frontmatter of skills/<name>.md."""

    name: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    use_when: str
    tools: list[str] = Field(default_factory=list)
    data: list[str] = Field(default_factory=list)
    escalate_if: str | None = None


class Case(BaseModel):
    """A row in the human queue (escalation) or an uncovered question."""

    id: int
    kind: Literal["escalation", "uncovered"]
    status: Literal["open", "accepted", "resolved"]
    severity: Severity | None
    summary: str
    client_id: str | None
    client_name: str | None
    assigned_to: str | None
    visit: dict[str, Any] | None = None
    created_at: str
    updated_at: str | None


class CaseAction(BaseModel):
    by: str = Field(min_length=1)
    note: str | None = None


class CheckinRequest(BaseModel):
    client_id: str = Field(min_length=1, max_length=100)


class CheckinResponse(BaseModel):
    """Start of an outbound Check-in. Grace's session gets these as dynamic variables."""

    call_id: str
    client_id: str
    client_name: str
