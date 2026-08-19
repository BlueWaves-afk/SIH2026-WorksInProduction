"""AlertCase — produced by M5 (case workflow), consumed by M6/M7/M8.

M5 owns `status`. M6 owns delivery status separately (see DeliveryAttempt).
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .risk_event import Band


class CaseStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    VISITED = "visited"
    REFERRED = "referred"
    RESOLVED = "resolved"


class AlertCase(BaseModel):
    case_id: str
    event_id: str
    farmer_token: str
    village_id: str
    recipient_role: str = Field(..., examples=["extension_officer"])
    band: Band
    confidence: float = Field(..., ge=0, le=1)
    assigned_to: str | None = None
    channel_preferences: list[str] = Field(default_factory=list)
    status: CaseStatus = CaseStatus.NEW
    sent_at: datetime | None = None
    ack_at: datetime | None = None
    sla_due_at: datetime | None = None
    resolution_code: str | None = None
    notes: str | None = None
