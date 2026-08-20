"""Alert-fatigue guardrails."""

from datetime import datetime


def within_daily_cap(sent_count: int, cap: int) -> bool:
    return sent_count < cap


def quiet_hours(now: datetime, start: int = 21, end: int = 7) -> bool:
    return now.hour >= start or now.hour < end if start > end else start <= now.hour < end
