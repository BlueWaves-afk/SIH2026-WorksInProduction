"""Stable M3 adapter contracts.

The adapters package deliberately contains no database or HTTP framework code. The
platform converts these DTOs to its canonical ``Observation`` schema at the M1
boundary. Mock and real implementations therefore remain interchangeable.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class AdapterMode(str, Enum):
    MOCK = "mock"
    REAL = "real"


class SignalRequest(BaseModel):
    village_id: str | None = None
    district_id: str | None = None
    mandi_id: str | None = None
    commodity: str | None = None
    date_range: tuple[date, date]


class RawPayload(BaseModel):
    source: str
    fetched_at: datetime
    body: dict[str, Any]


class ObservationPayload(BaseModel):
    """M3 transport DTO; M1 maps it to its canonical Observation schema."""

    source: str
    observed_at: datetime
    village_id: str | None = None
    plot_grid: str | None = None
    metric: str
    value: Any
    unit: str = ""
    quality: Literal["good", "degraded", "stale", "missing"] = "good"
    ttl: timedelta = timedelta(days=2)


class ProfilePrefill(BaseModel):
    farmer_ref: str
    village_id: str
    crop: str | None = None
    land_area_band: str | None = None
    irrigation_type: str | None = None
    source: Literal["agristack"] = "agristack"
    fetched_at: datetime


class ASRResult(BaseModel):
    text: str
    lang: str
    confidence: float = Field(ge=0, le=1)


class SignalAdapter(Protocol):
    source: str
    mode: AdapterMode

    def fetch(self, req: SignalRequest) -> list[ObservationPayload]: ...

    def health(self): ...


class ProfileAdapter(Protocol):
    source: Literal["agristack"]
    mode: AdapterMode

    def fetch_profile(self, consent: Any, farmer_ref: str) -> ProfilePrefill: ...

    def health(self): ...


class VoiceAdapter(Protocol):
    source: Literal["bhashini"]
    mode: AdapterMode

    def transcribe(self, audio: bytes, lang: str) -> ASRResult: ...

    def synthesize(self, text: str, lang: str) -> bytes: ...

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str: ...

    def health(self): ...


__all__ = [
    "ASRResult",
    "AdapterMode",
    "ObservationPayload",
    "ProfileAdapter",
    "ProfilePrefill",
    "RawPayload",
    "SignalAdapter",
    "SignalRequest",
    "VoiceAdapter",
]
