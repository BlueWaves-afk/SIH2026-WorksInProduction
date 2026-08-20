"""PWA push provider boundary."""

from .base import NotificationProvider


class PushProvider(NotificationProvider):
    channel = "push"

    def send(self, destination: str, payload: dict) -> dict:
        del destination, payload
        raise NotImplementedError("Bind VAPID provider during deployment")

    def get_status(self, provider_reference: str) -> dict:
        return {"provider_reference": provider_reference, "status": "unknown"}
