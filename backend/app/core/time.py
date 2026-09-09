from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

INDIA = ZoneInfo("Asia/Kolkata")


def utc_datetime(value: datetime) -> datetime:
    """Interpret naive marketplace input as India time and store/compare in UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=INDIA)
    return value.astimezone(UTC)


def india_now() -> datetime:
    return datetime.now(UTC).astimezone(INDIA)
