"""SLA helpers used by the API and scheduled scanner."""

from datetime import datetime, timedelta


def ack_due_at(created_at: datetime, band: str) -> datetime:
    return created_at + timedelta(hours=8 if band.lower() == "red" else 24)


def is_breached(*, status: str, due_at: datetime | None, now: datetime | None = None) -> bool:
    return status.lower() in {"new", "acknowledged"} and due_at is not None and due_at < (now or datetime.utcnow())
