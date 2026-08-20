"""Voice provider boundary; Bhashini audio is supplied by M3."""

from .base import NotificationProvider


class VoiceProvider(NotificationProvider):
    channel = "voice"

    def send(self, destination: str, payload: dict) -> dict:
        del destination, payload
        raise NotImplementedError("Bind the approved voice provider here")

    def get_status(self, provider_reference: str) -> dict:
        return {"provider_reference": provider_reference, "status": "unknown"}
