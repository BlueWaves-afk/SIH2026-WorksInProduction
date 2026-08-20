"""Locale fallback for pre-approved cards."""


def resolve_card(cards: list[dict], locale: str, fallback: str = "en") -> dict | None:
    return next((card for card in cards if card.get("locale") == locale), None) or next((card for card in cards if card.get("locale") == fallback), None)
