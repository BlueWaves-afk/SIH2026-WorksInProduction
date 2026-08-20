"""Template fill + optional polish. Draft only, never sends."""


def draft_message(*, locale: str, band: str, village: str) -> str:
    del locale
    return f"Namaskar. We noticed a {band} support signal in {village}. An officer will contact you. This is not a credit score."
