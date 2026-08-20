"""No voice calls 21:00–07:00 IST; SMS is queued."""

from datetime import datetime


def is_quiet_hours(now: datetime, start: int = 21, end: int = 7) -> bool:
    return now.hour >= start or now.hour < end if start > end else start <= now.hour < end
