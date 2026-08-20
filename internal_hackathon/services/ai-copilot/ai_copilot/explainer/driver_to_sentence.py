"""Template-first driver narration; no score or agronomy inference happens here."""

from __future__ import annotations

from app.schemas import Contributor


def driver_to_sentence(driver: Contributor, locale: str = "en") -> str:
    """Return the upstream explanation verbatim with a locale-safe prefix."""

    prefixes = {"hi": "मुख्य संकेत: ", "mr": "मुख्य संकेत: ", "en": "Key signal: "}
    return f"{prefixes.get(locale, prefixes['en'])}{driver.explanation}."
