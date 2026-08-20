"""Channel fallback policy."""


def next_channel(current: str, *, contact_consent: bool) -> str | None:
    if not contact_consent:
        return None
    return {"voice": "sms", "sms": "push", "push": None}.get(current)
