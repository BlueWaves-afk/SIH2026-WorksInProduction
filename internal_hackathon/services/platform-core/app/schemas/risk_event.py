"""RiskEvent — produced by M4 (scoring), consumed by M5/M6/M7/M8.

This is the output of a *deterministic rules engine*, not a model.
It is explicitly NOT a credit, loan-default, or insurance score.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

SCORE_DISCLAIMER = "This is not a credit, loan-default, or insurance score."


class Band(str, Enum):
    GREEN = "green"    # <50 (CRIDA low)
    AMBER = "amber"    # 50-69 (CRIDA moderate)
    RED = "red"        # >=70 (CRIDA severe)


class Contributor(BaseModel):
    """One driver of the score — the human-readable 'why'."""
    signal: str = Field(..., examples=["rainfall_shock", "price_stress"])
    points: float
    max_points: float
    explanation: str = Field(..., examples=["Rainfall 28% below normal"])
    source: str
    observed_at: datetime


class RiskEvent(BaseModel):
    event_id: str
    farmer_token: str
    village_id: str
    score: float = Field(..., ge=0, le=100)
    band: Band
    confidence: float = Field(..., ge=0, le=1)
    contributors: list[Contributor] = Field(default_factory=list)
    action_ids: list[str] = Field(default_factory=list)
    model_version: str
    evaluated_at: datetime | None = None
    expires_at: datetime
    disclaimer: str = SCORE_DISCLAIMER
    context_flags: list[str] = Field(default_factory=list)

    def top_drivers(self, n: int = 3) -> list[Contributor]:
        return sorted(self.contributors, key=lambda c: c.points, reverse=True)[:n]
