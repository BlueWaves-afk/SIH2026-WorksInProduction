"""Provider protocol used by mock and real channel adapters."""

from typing import Protocol


class NotificationProvider(Protocol):
    channel: str

    def send(self, destination: str, payload: dict) -> dict: ...

    def get_status(self, provider_reference: str) -> dict: ...
