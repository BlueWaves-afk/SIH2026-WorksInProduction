"""Pure scoring types.

The scoring package deliberately owns a small type-only boundary so it can be tested without
FastAPI, SQLAlchemy, a database, or live adapters.  M1's Pydantic contracts mirror these fields and
perform the HTTP boundary conversion.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field


class Observation(BaseModel):
    source: str
    observed_at: datetime
    village_id: str | None = None
    plot_grid: str | None = None
    metric: str
    value: Any
    unit: str = ""
    quality: str = "good"
    ttl: timedelta = timedelta(days=2)

    def is_stale(self, now: datetime) -> bool:
        return (now - self.observed_at) > self.ttl


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


class FarmerContext(BaseModel):
    farmer_token: str
    village_id: str
    crop: str
    sowing_date: date | None = None
    irrigation_type: Literal["rainfed", "partial", "assured"] = "rainfed"
    area_band: Literal["<1", "1-2", ">2"] | None = None
    secondary_crop: str | None = None
    schemes_enrolled: list[str] = Field(default_factory=list)
    institutional_access: Literal["good", "limited", "unknown"] = "unknown"
    soil_retention: Literal["poor", "medium", "good", "unknown"] = "unknown"


@dataclass(frozen=True)
class SubScoreResult:
    signal: str
    points: float
    max_points: float
    applicable: bool
    stale: bool
    freshness: float
    rule_id: str
    source: str
    observed_at: datetime | None
    driver_text: str | None


@dataclass(frozen=True)
class BandDecision:
    confirmed_band: Literal["green", "amber", "red"]
    raw_band: Literal["green", "amber", "red"]
    pending_band: str | None
    pending_since: datetime | None
    pending_observation_count: int
    suppressed_escalation: bool


class Contributor(BaseModel):
    signal: str
    points: float
    max_points: float
    explanation: str
    source: str
    observed_at: datetime


class RiskEvent(BaseModel):
    event_id: str
    farmer_token: str
    village_id: str
    score: float = Field(ge=0, le=100)
    band: Literal["green", "amber", "red"]
    confidence: float = Field(ge=0, le=1)
    contributors: list[Contributor] = Field(default_factory=list)
    action_ids: list[str] = Field(default_factory=list)
    model_version: str
    evaluated_at: datetime | None = None
    expires_at: datetime
    disclaimer: str
    context_flags: list[str] = Field(default_factory=list)
