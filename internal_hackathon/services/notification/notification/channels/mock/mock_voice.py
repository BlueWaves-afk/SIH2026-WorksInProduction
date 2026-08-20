"""Mock voice provider (default)."""

class MockVoiceProvider:
    channel = "voice"

    def send(self, destination: str, payload: dict) -> dict:
        return {"status": "queued", "provider_reference": f"mock-voice:{destination[-4:]}", "payload": payload}

    def get_status(self, provider_reference: str) -> dict:
        return {"status": "queued", "provider_reference": provider_reference}
