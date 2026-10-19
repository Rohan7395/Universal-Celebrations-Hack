"""FastAPI entry point. Serves the API under /api and the static dashboard from web/ if present."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import flag
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Care Team", version="0.1.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(flag.router, prefix="/api")

    # Mounted last so /api routes win; web/ is Person B's and may not exist yet.
    if settings.web_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.web_dir, html=True), name="web")
    return app


app = create_app()
