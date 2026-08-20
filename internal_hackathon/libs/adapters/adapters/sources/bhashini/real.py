from .._common import MockVoiceAdapter


class BhashiniRealAdapter(MockVoiceAdapter):
    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        raise RuntimeError("Bhashini real adapter requires a configured API key")
