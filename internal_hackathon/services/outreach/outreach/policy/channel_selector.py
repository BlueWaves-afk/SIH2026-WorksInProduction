"""Channel ladder selection."""


def select_channel(*, band: str, consent: dict[str, bool], has_voice: bool = True, has_sms: bool = True) -> str | None:
    if not consent.get("contact", consent.get("contact_me", False)):
        return None
    if band.lower() == "red" and has_voice:
        return "voice"
    if has_sms:
        return "sms"
    return "push" if consent.get("storage", False) else None
