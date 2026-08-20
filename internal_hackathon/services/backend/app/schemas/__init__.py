"""Canonical HTTP contracts for the unified KisanSetu backend."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .farmer import ConsentFlags, FarmerProfile, FarmerProfileCreate, FarmerProfilePublic


class Band(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class Contributor(BaseModel):
    signal: str
    points: float
    max_points: float
    explanation: str
    source: str
    observed_at: datetime


class RiskEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    farmer_token: str
    village_id: str
    score: float = Field(ge=0, le=100)
    band: Band
    confidence: float = Field(ge=0, le=1)
    contributors: list[Contributor] = Field(default_factory=list)
    action_ids: list[str] = Field(default_factory=list)
    model_version: str
    evaluated_at: datetime | None = None
    expires_at: datetime
    disclaimer: str = "This is not a credit, loan-default, or insurance score."
    context_flags: list[str] = Field(default_factory=list)

    def top_drivers(self, n: int = 3) -> list[Contributor]:
        return sorted(self.contributors, key=lambda item: item.points, reverse=True)[:n]


class CaseStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    VISITED = "visited"
    REFERRED = "referred"
    RESOLVED = "resolved"


class AlertCase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    event_id: str
    farmer_token: str
    village_id: str
    recipient_role: str = "extension_officer"
    band: Band
    confidence: float = Field(ge=0, le=1)
    assigned_to: str | None = None
    channel_preferences: list[str] = Field(default_factory=list)
    status: CaseStatus = CaseStatus.NEW
    sent_at: datetime | None = None
    ack_at: datetime | None = None
    sla_due_at: datetime | None = None
    sla_breached: bool = False
    sla_breached_at: datetime | None = None
    resolution_code: str | None = None
    notes: str | None = None


class Citation(BaseModel):
    source_doc: str
    chunk_id: str
    quote: str


class SchemeMatch(BaseModel):
    scheme: str
    why: str
    citations: list[Citation] = Field(default_factory=list)
    verified: bool = False


class CopilotBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    scheme_matches: list[SchemeMatch] = Field(default_factory=list)
    suggested_action: str | None = None
    draft_message: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    model_version: str | None = None


class ObservationCreate(BaseModel):
    farmer_token: str
    source: str = Field(min_length=1, max_length=64)
    observed_at: datetime
    village_id: str | None = None
    plot_grid: str | None = None
    metric: str = Field(min_length=1, max_length=96)
    value: Any
    unit: str = ""
    quality: str = Field(default="good", pattern="^(good|degraded|stale|missing)$")
    ttl_seconds: int = Field(default=172800, ge=1, le=31_536_000)


class RecalculateRequest(BaseModel):
    farmer_token: str
    as_of: datetime | None = None
    source_mode: str = Field(default="stored", pattern="^(stored|live)$")


class LiveIngestionPreviewRequest(BaseModel):
    village_id: str | None = None
    district_id: str | None = None
    mandi_id: str | None = None
    commodity: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sources: list[str] = Field(default_factory=lambda: ["imd", "agmarknet"])


class ReplayRequest(BaseModel):
    farmer_token: str
    scenario: str = Field(
        default="normal",
        pattern="^(normal|rainfall_shock|price_crash|due_window|stale_data|drought|drought_crash)$",
    )
    day_offset: int = Field(default=0, ge=0, lt=90)


class CaseResolveRequest(BaseModel):
    resolution_code: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)


class CaseTransitionRequest(BaseModel):
    status: CaseStatus
    reason: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class CopilotBriefRequest(BaseModel):
    case_id: int
    locale: str = Field(default="en", min_length=2, max_length=8)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class CopilotConversationRequest(BaseModel):
    farmer_token: str = Field(min_length=1, max_length=160)
    message: str = Field(min_length=1, max_length=2000)
    locale: str = Field(default="en", min_length=2, max_length=8)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=12)


class CopilotConversationResponse(BaseModel):
    reply: str
    provider: str
    model: str
    safe_fallback: bool
    citations: list[Citation] = Field(default_factory=list)
    event_id: str | None = None
    disclaimer: str = "This is a support signal, not a credit, loan-default, or insurance score."


class NotificationDispatchRequest(BaseModel):
    case_id: int
    channel: str = Field(default="sms", pattern="^(sms|voice|push)$")
    content: dict[str, Any] = Field(default_factory=dict)


class ConsentUpdate(BaseModel):
    storage: bool | None = None
    contact: bool | None = None
    analytics: bool | None = None
    due_window: bool | None = None
    version: str = "1"


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


class ConsentContext(BaseModel):
    farmer_token: str
    storage: bool = False
    contact: bool = False
    analytics: bool = False
    due_window: bool = False
    consent_scopes: list[str] = Field(default_factory=list)
    version: str = "1"

    def may_contact(self) -> bool:
        return self.storage and self.contact


__all__ = [
    "AlertCase",
    "Band",
    "CaseResolveRequest",
    "CaseStatus",
    "CaseTransitionRequest",
    "Citation",
    "ConsentContext",
    "ConsentFlags",
    "ConsentUpdate",
    "Contributor",
    "CopilotBrief",
    "ConversationMessage",
    "CopilotConversationRequest",
    "CopilotConversationResponse",
    "FarmerProfile",
    "FarmerProfileCreate",
    "FarmerProfilePublic",
    "NotificationDispatchRequest",
    "LiveIngestionPreviewRequest",
    "ObservationCreate",
    "Page",
    "RecalculateRequest",
    "ReplayRequest",
    "RiskEvent",
    "SchemeMatch",
]
