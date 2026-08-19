"""ActionCard — agronomist-authored offline, rendered by M6, shown by M8.

Content is *pre-approved template text only*. The platform never generates
agronomy advice, pesticide dosage, or diagnosis at runtime.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ActionStep(BaseModel):
    text: str
    audio_key: str | None = None      # pre-rendered/TTS cache key for voice playback
    deep_link: str | None = None      # e.g. mandi-compare, scheme info


class ActionCard(BaseModel):
    card_id: str
    locale: str = Field(..., examples=["hi", "mr"])
    title: str
    steps: list[ActionStep] = Field(default_factory=list)
    scheme_refs: list[str] = Field(default_factory=list)
    approved_by: str = Field(..., description="Agronomist/reviewer of record")
    version: str = "1"
    effective_from: date | None = None
    expires_on: date | None = None
    crop_codes: list[str] = Field(default_factory=list)
    region_codes: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    content_hash: str | None = None
