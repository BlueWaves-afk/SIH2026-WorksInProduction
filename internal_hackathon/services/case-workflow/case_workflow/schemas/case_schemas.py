"""Transport schemas used by backend adapters."""

from datetime import datetime

from pydantic import BaseModel


class CaseTransition(BaseModel):
    status: str
    reason: str | None = None
    notes: str | None = None


class CaseSnapshot(BaseModel):
    case_id: str
    farmer_token: str
    village_id: str
    band: str
    status: str
    sla_due_at: datetime | None = None
