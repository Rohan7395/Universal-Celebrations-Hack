"""GET /api/stream: the room feed as Server-Sent Events.

A fresh connection replays the recent room; a reconnect sends Last-Event-ID and gets only
what it missed. New rows are polled from SQLite, which also picks up background tasks' posts.
"""

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from app.api.models import RoomMessage
from app.config import settings
from app.db.database import db
from app.engine import room

router = APIRouter()

POLL_S = 0.3
KEEPALIVE_S = 15.0
REPLAY = 50


def format_sse(msg: RoomMessage) -> str:
    return f"id: {msg.id}\nevent: room\ndata: {msg.model_dump_json()}\n\n"


async def room_events(
    tenant: str,
    last_id: int | None,
    is_disconnected: Callable[[], Awaitable[bool]],
    poll_s: float = POLL_S,
) -> AsyncIterator[str]:
    with db() as conn:
        backlog = room.recent(conn, tenant, REPLAY) if last_id is None else []
        if last_id is None:
            last_id = backlog[-1].id if backlog else 0
    yield "retry: 2000\n\n"
    for msg in backlog:
        yield format_sse(msg)
    last_sent = time.monotonic()
    while not await is_disconnected():
        with db() as conn:
            new = room.fetch_after(conn, tenant, last_id or 0)
        for msg in new:
            last_id = msg.id
            yield format_sse(msg)
            last_sent = time.monotonic()
        if time.monotonic() - last_sent > KEEPALIVE_S:
            yield ": keepalive\n\n"
            last_sent = time.monotonic()
        await asyncio.sleep(poll_s)


@router.get("/stream")
async def stream(
    request: Request,
    last_event_id: str | None = Header(default=None),
    after: int | None = None,
) -> StreamingResponse:
    last = after if after is not None else (int(last_event_id) if last_event_id else None)
    return StreamingResponse(
        room_events(settings.tenant_id, last, request.is_disconnected),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/messages", response_model=list[RoomMessage])
def messages(after: int = 0, limit: int = 200) -> list[RoomMessage]:
    """The same feed as plain JSON, for tests and debugging."""
    with db() as conn:
        return room.fetch_after(conn, settings.tenant_id, after, min(limit, 500))
