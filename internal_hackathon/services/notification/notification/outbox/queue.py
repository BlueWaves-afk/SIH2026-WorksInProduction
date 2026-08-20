"""In-memory outbox reference implementation for unit tests."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from .idempotency import idempotency_key


@dataclass
class OutboxEntry:
    farmer_token: str
    channel: str
    payload: dict
    key: str
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class Outbox:
    def __init__(self):
        self.entries: dict[str, OutboxEntry] = {}

    def enqueue(self, farmer_token: str, channel: str, payload: dict, event_id: str) -> OutboxEntry:
        key = idempotency_key(farmer_token, channel, event_id)
        return self.entries.setdefault(key, OutboxEntry(farmer_token, channel, payload, key))
