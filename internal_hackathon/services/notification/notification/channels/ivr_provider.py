"""IVR fallback provider boundary."""

from .base import NotificationProvider


class IVRProvider(NotificationProvider):
    channel = "ivr"

    def send(self, destination: str, payload: dict) -> dict:
        del destination, payload
        raise NotImplementedError("Bind IVR provider during deployment")

    def get_status(self, provider_reference: str) -> dict:
        return {"provider_reference": provider_reference, "status": "unknown"}
