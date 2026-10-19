"""Settings read from .env. The Gemini model IDs are pinned here and nowhere else."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Pinned Gemini model IDs. Override with GEMINI_MODEL / GEMINI_FALLBACK_MODEL only to test a swap.
GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", GEMINI_MODEL))
    gemini_fallback_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_FALLBACK_MODEL", GEMINI_FALLBACK_MODEL)
    )
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_agent_id: str = field(default_factory=lambda: os.getenv("ELEVENLABS_AGENT_ID", ""))
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", str(ROOT / "data" / "care.sqlite")))
    )
    tenant_id: str = field(default_factory=lambda: os.getenv("TENANT_ID", "brightdays"))
    web_dir: Path = ROOT / "web"


settings = Settings()
