"""Wire shape for the platform-owned outbox table."""

from pydantic import BaseModel


class OutboxEntry(BaseModel):
    message_id: str
    farmer_token: str
    channel: str
    status: str = "pending"
