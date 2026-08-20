"""Auditable outreach decision record."""

from datetime import UTC, datetime


def log_decision(*, farmer_token: str, trigger: str, channel: str | None, outcome: str, suppressed_reason: str | None = None) -> dict:
    return {"farmer_token": farmer_token, "trigger": trigger, "channel": channel, "outcome": outcome, "suppressed_reason": suppressed_reason, "created_at": datetime.now(UTC).isoformat()}
