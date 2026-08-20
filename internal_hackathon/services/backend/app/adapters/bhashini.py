"""Compatibility import for the canonical M3 Bhashini adapter."""

from app.integrations.canonical import _ensure_workspace_packages

_ensure_workspace_packages()
from adapters.sources.bhashini import BhashiniMockAdapter  # noqa: E402


class BhashiniAdapter:
    def __init__(self):
        self._adapter = BhashiniMockAdapter()

    def translate_text(self, text: str, target_lang: str):
        return self._adapter.translate(text, "en", target_lang)
