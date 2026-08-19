"""DeliveryAttempt — produced by M6, read by M5 (timeline), M7, M8.

M6 writes only this; it never mutates AlertCase.status (owned by M5).
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Channel(str, Enum):
    """Ordered by REACH, not richness (module_9 §9).

    SMS and IVR reach any phone with no internet; IVR needs no literacy.
    Email is deliberately absent — it is an officer channel, not a farmer channel.
    """
    SMS = "sms"            # 1 - backbone, any phone, no internet
    IVR = "ivr"            # 2 - accessibility hero, no literacy needed
    VOICE = "voice"        # 2 - outbound TTS call
    WHATSAPP = "whatsapp"  # 3 - smartphones, rich media
    PUSH = "push"          # 4 - only if PWA installed, additive only


class DeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SUPPRESSED = "suppressed"   # consent withheld or daily cap hit


class DeliveryAttempt(BaseModel):
    delivery_id: str
    event_id: str | None = None
    case_id: str | None = None
    channel: Channel
    locale: str
    status: DeliveryStatus = DeliveryStatus.QUEUED
    attempted_at: datetime | None = None
    delivered_at: datetime | None = None
    provider_ref: str | None = None
    failure_reason: str | None = None
