"""FastAPI entry point. Serves the API under /api and the static dashboard from web/ if present."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import cases, checkins, controls, eleven, flag, stream
from app.config import settings
from app.db.database import ensure_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Care Team", version="0.1.0", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for module in (flag, stream, cases, controls, checkins, eleven):
        app.include_router(module.router, prefix="/api")

    # Mounted last so /api routes win.
    if settings.web_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.web_dir, html=True), name="web")
    return app


app = create_app()
