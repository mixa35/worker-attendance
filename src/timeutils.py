"""Local-time helpers (Asia/Tbilisi by default, configurable via TZ)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings


def tz() -> ZoneInfo:
    return ZoneInfo(settings.tz)


def now_local() -> datetime:
    return datetime.now(tz())


def today_iso() -> str:
    return now_local().date().isoformat()
