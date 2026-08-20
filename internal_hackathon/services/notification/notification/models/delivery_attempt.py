"""Wire shape for a provider attempt."""

from pydantic import BaseModel


class DeliveryAttempt(BaseModel):
    message_id: str
    channel: str
    status: str
    provider_reference: str | None = None
