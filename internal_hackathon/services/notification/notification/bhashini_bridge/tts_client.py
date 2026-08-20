"""Thin, stateless bridge over a configured Bhashini adapter."""


def render_voice(text: str, lang: str, adapter) -> bytes:
    return adapter.synthesize(text, lang)
