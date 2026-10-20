"""Tenant-local time. DEMO_NOW pins the time of day so a demo books the same slots at any hour."""

from datetime import datetime

from app.config import settings


def now() -> datetime:
    real = datetime.now()
    if not settings.demo_now:
        return real
    pinned = datetime.strptime(settings.demo_now, "%H:%M").time()
    return datetime.combine(real.date(), pinned)
