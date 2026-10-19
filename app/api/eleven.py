"""GET /api/eleven/signed-url: a short-lived session URL for Grace (BUILD-PLAN §6).

Grace's agent has auth turned on, so the browser never sees the API key or starts a
session on its own; it asks this endpoint, which asks ElevenLabs.
"""

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter()

ELEVENLABS_SIGNED_URL = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"


@router.get("/eleven/signed-url")
def signed_url() -> dict[str, str]:
    if not settings.elevenlabs_api_key or not settings.elevenlabs_agent_id:
        raise HTTPException(
            503, "ElevenLabs is not configured: set ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID"
        )
    try:
        response = httpx.get(
            ELEVENLABS_SIGNED_URL,
            params={"agent_id": settings.elevenlabs_agent_id},
            headers={"xi-api-key": settings.elevenlabs_api_key},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Could not reach ElevenLabs: {exc.__class__.__name__}") from exc
    if response.status_code != 200:
        raise HTTPException(502, f"ElevenLabs returned {response.status_code}")
    return {"signed_url": response.json()["signed_url"]}
