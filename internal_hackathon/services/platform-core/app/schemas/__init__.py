"""Shared cross-module contracts (module_0 §4). Import from here — never redefine.

    from app.schemas import Observation, RiskEvent, AlertCase
"""
from .action_card import ActionCard, ActionStep
from .alert_case import AlertCase, CaseStatus
from .auth_context import AuthContext, Role
from .consent_context import ConsentContext
from .copilot_brief import Citation, CopilotBrief, SchemeMatch
from .delivery_attempt import Channel, DeliveryAttempt, DeliveryStatus
from .envelope import ErrorEnvelope, Page
from .observation import Observation, Quality
from .outreach import (
    InboundEvent,
    Intent,
    OutreachDecision,
    SuppressedReason,
    Trigger,
)
from .risk_event import Band, Contributor, RiskEvent

__all__ = [
    "ActionCard",
    "ActionStep",
    "AlertCase",
    "AuthContext",
    "Band",
    "CaseStatus",
    "Channel",
    "Citation",
    "ConsentContext",
    "Contributor",
    "CopilotBrief",
    "DeliveryAttempt",
    "DeliveryStatus",
    "ErrorEnvelope",
    "InboundEvent",
    "Intent",
    "Observation",
    "OutreachDecision",
    "Page",
    "Quality",
    "RiskEvent",
    "Role",
    "SchemeMatch",
    "SuppressedReason",
    "Trigger",
]
