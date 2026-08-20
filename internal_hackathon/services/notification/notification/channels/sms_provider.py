"""Real SMS provider boundary; provider credentials remain external."""

from .base import NotificationProvider


class SMSProvider(NotificationProvider):
    channel = "sms"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def send(self, destination: str, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("SMS provider key is not configured")
        raise NotImplementedError("Bind the approved telecom provider here")

    def get_status(self, provider_reference: str) -> dict:
        return {"provider_reference": provider_reference, "status": "unknown"}
