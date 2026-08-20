"""Deterministic officer queue ordering."""

from datetime import datetime


ORDER = {"red": 0, "amber": 1, "green": 2}


def rank_cases(cases: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.utcnow()
    return sorted(cases, key=lambda item: (ORDER.get(str(item.get("band", "green")).lower(), 3), -float(item.get("confidence", 0)), item.get("sla_due_at") or "", item.get("created_at") or ""))
