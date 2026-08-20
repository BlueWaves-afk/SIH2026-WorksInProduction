"""Read-only in-memory audit query helper for adapters and tests."""


def filter_audit_events(events: list[dict], *, target_id: str | None = None, action: str | None = None) -> list[dict]:
    return [event for event in events if (target_id is None or event.get("target_id") == target_id) and (action is None or event.get("action") == action)]
