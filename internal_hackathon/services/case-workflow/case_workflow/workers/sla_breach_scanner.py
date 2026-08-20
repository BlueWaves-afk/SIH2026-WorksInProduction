"""Periodic SLA scan helper."""

from datetime import datetime

from ..domain.sla import is_breached


def breached_cases(cases: list[dict], now: datetime | None = None) -> list[dict]:
    return [case for case in cases if is_breached(status=case.get("status", "new"), due_at=case.get("sla_due_at"), now=now)]
