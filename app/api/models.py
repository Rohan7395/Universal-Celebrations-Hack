"""Pydantic models for the frozen contracts in docs/BUILD-PLAN.md §4."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Guardian Severity, lowest to highest. Compare with `rank`, not string order."""

    ROUTINE = "routine"
    WATCH = "watch"
    URGENT = "urgent"
    EMERGENCY = "emergency"

    @property
    def rank(self) -> int:
        return list(Severity).index(self)


class FlagRequest(BaseModel):
    """What Grace's `flag` client tool sends. ElevenLabs may not supply a call_id."""

    client_id: str = Field(min_length=1)
    what_was_said: str = Field(min_length=1)
    call_id: str | None = None


class FlagResponse(BaseModel):
    severity: Severity
    actions: list[str] = Field(default_factory=list)
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
    created_at: str | None = None


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


class SkillFrontmatter(BaseModel):
    """The YAML frontmatter of skills/<name>.md."""

    name: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    use_when: str
    tools: list[str] = Field(default_factory=list)
    data: list[str] = Field(default_factory=list)
    escalate_if: str | None = None
