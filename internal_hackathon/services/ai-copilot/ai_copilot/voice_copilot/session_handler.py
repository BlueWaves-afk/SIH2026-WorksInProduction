"""Bridges Bhashini calls to deterministic narration."""


def narrate(text: str, *, language: str, voice_adapter) -> bytes:
    return voice_adapter.synthesize(text, language)
