"""Outreach contracts — produced by M9 (outreach automation).

M9 decides *whether, when and by which channel*; M6 executes the send.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .delivery_attempt import Channel
from .risk_event import Band


class Trigger(str, Enum):
    BAND_CHANGE = "band_change"
    SUSTAINED_RED = "sustained_red"
    FARMER_REQUESTED = "farmer_requested"


class SuppressedReason(str, Enum):
    NONE = "none"
    CONSENT = "consent"
    CAP = "cap"
    QUIET_HOURS = "quiet_hours"
    LOW_CONFIDENCE = "low_confidence"


class Intent(str, Enum):
    REQUEST_CALLBACK = "request_callback"
    REPORT_DAMAGE = "report_damage"
    REPORT_NO_BUYER = "report_no_buyer"
    OPT_OUT = "opt_out"


class OutreachDecision(BaseModel):
    """Why we did (or did not) contact a farmer. Every decision is logged, including suppressions."""
    decision_id: str
    farmer_token: str
    event_id: str | None = None
    trigger: Trigger
    from_band: Band | None = None
    to_band: Band | None = None
    channel_plan: list[Channel] = Field(default_factory=list)
    suppressed_reason: SuppressedReason = SuppressedReason.NONE
    decided_at: datetime

    @property
    def was_sent(self) -> bool:
        return self.suppressed_reason is SuppressedReason.NONE


class InboundEvent(BaseModel):
    """An app-free return path: missed call, IVR keypress, or SMS reply.

    Normalised into a `farmer_report` Observation so the scoring engine treats
    farmer-initiated signals identically to machine-collected ones.
    """
    inbound_id: str
    channel: Channel
    from_number_token: str        # tokenised, never a raw phone number
    payload: str | None = None
    intent: Intent
    received_at: datetime
