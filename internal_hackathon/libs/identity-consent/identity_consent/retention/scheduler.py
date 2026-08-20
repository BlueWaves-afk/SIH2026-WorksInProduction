"""Retention policy helper; the platform supplies the delete callback."""

from datetime import UTC, datetime, timedelta
from collections.abc import Callable


def purge_expired(records: list[dict], *, ttl_days: int, now: datetime | None = None, delete: Callable[[dict], None] | None = None) -> int:
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=ttl_days)
    expired = [record for record in records if record.get("created_at") and record["created_at"] < cutoff]
    for record in expired:
        if delete:
            delete(record)
    return len(expired)
