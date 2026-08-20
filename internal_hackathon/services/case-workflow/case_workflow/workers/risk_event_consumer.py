"""Idempotent worker decision; persistence is delegated to the repository."""

from ..domain.dedup import deduplicate_open_cases


def cases_for_risk_event(event: dict, open_cases: list[dict]) -> list[dict]:
    candidate = {"event_id": event["event_id"], "farmer_token": event["farmer_token"], "band": event["band"], "score": event["score"], "status": "new"}
    return deduplicate_open_cases([*open_cases, candidate])
