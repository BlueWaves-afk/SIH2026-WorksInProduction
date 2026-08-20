from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.case import AlertCase
from app.models.consent import ConsentLedger
from app.models.farmer import FarmerProfile
from app.models.history import DeliveryAttempt
from app.models.outbox import OutboxMessage
from app.models.observation import Observation
from app.schemas import NotificationDispatchRequest
from app.security import AuthContext, require_roles
from app.security.audit import record_audit

router = APIRouter()


@router.post("/dispatch")
def dispatch_notification(
    payload: NotificationDispatchRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin")),
):
    case = db.query(AlertCase).filter(AlertCase.id == payload.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == case.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    flags = profile.consent_flags or {}
    if not bool(flags.get("contact_me", flags.get("contact", False))) or not bool(flags.get("store_data", flags.get("storage", False))):
        raise HTTPException(status_code=403, detail="Contact consent is required")
    message = OutboxMessage(
        message_id=str(uuid4()),
        idempotency_key=f"case:{case.id}:manual:{payload.channel}",
        farmer_token=case.farmer_token,
        farmer_phone=profile.phone_enc,
        channel=payload.channel,
        content=payload.content,
        status="pending",
        consent_required="contact",
    )
    db.add(message)
    record_audit(db, actor=actor, action="notification.enqueue", target_id=str(case.id), details={"channel": payload.channel})
    db.commit()
    return {"message_id": message.message_id, "status": message.status, "channel": message.channel}


@router.get("/{message_id}/status")
def notification_status(message_id: str, db: Session = Depends(get_db), _: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor"))):
    message = db.query(OutboxMessage).filter(OutboxMessage.message_id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    attempts = db.query(DeliveryAttempt).filter(DeliveryAttempt.message_id == message_id).order_by(DeliveryAttempt.attempted_at.asc()).all()
    return {"message_id": message_id, "status": message.status, "attempts": [{"status": item.status, "channel": item.channel, "attempted_at": item.attempted_at, "error": item.error} for item in attempts]}


@router.post("/webhooks/provider")
def provider_webhook(
    payload: dict,
    provider_signature: str | None = Header(default=None, alias="X-Provider-Signature"),
    db: Session = Depends(get_db),
):
    raw_message = str(payload.get("message_id", ""))
    supplied = (provider_signature or "").removeprefix("sha256=")
    if settings.sms_provider_key:
        expected = hmac.new(settings.sms_provider_key.encode(), raw_message.encode(), hashlib.sha256).hexdigest()
        if not supplied or not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=401, detail="Invalid provider signature")
    elif settings.env.lower() not in {"local", "test"}:
        raise HTTPException(status_code=503, detail="Provider webhook secret is not configured")
    message_id = raw_message
    message = db.query(OutboxMessage).filter(OutboxMessage.message_id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    status = str(payload.get("status", "unknown"))
    message.status = status
    db.add(DeliveryAttempt(message_id=message_id, channel=message.channel, status=status, provider_reference=payload.get("provider_reference"), error=payload.get("error")))
    db.commit()
    return {"message_id": message_id, "status": status}


@router.post("/webhooks/inbound")
def inbound_webhook(
    payload: dict,
    provider_signature: str | None = Header(default=None, alias="X-Provider-Signature"),
    db: Session = Depends(get_db),
):
    """Handle bounded SMS/missed-call/IVR callbacks without exposing phone numbers."""

    raw = f"{payload.get('event_type', '')}:{payload.get('farmer_token', '')}:{payload.get('message_id', '')}"
    supplied = (provider_signature or "").removeprefix("sha256=")
    if settings.sms_provider_key:
        expected = hmac.new(settings.sms_provider_key.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not supplied or not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=401, detail="Invalid provider signature")
    elif settings.env.lower() not in {"local", "test"}:
        raise HTTPException(status_code=503, detail="Provider webhook secret is not configured")
    farmer_token = str(payload.get("farmer_token", ""))
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    event_type = str(payload.get("event_type", "sms")).lower()
    flags = dict(profile.consent_flags or {})
    if event_type == "sms" and str(payload.get("text", "")).strip().upper() in {"STOP", "UNSUBSCRIBE"}:
        flags["contact_me"] = False
        profile.consent_flags = flags
        db.add(ConsentLedger(farmer_token=farmer_token, action="WITHDRAW", purpose="contact_me", proof={"source": "provider_webhook"}))
        db.add(Observation(farmer_token=farmer_token, source="outreach_inbound", observed_at=datetime.utcnow(), village_id=profile.village_id, metric="outreach_unanswered", value="contact withdrawn", unit="", quality="good", ttl=2592000))
        db.commit()
        return {"status": "contact_withdrawn", "farmer_token": farmer_token}
    if not bool(flags.get("store_data", flags.get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required for inbound records")
    if event_type in {"sms", "ivr"}:
        text_value = str(payload.get("text") or payload.get("keypress") or "REQUEST_HELP")[:280]
        db.add(Observation(farmer_token=farmer_token, source="outreach_inbound", observed_at=datetime.utcnow(), village_id=profile.village_id, metric="acute_farmer_report", value=text_value, unit="", quality="good", ttl=172800))
    elif event_type == "missed_call":
        if bool(flags.get("contact_me", flags.get("contact", False))):
            db.add(OutboxMessage(message_id=str(uuid4()), idempotency_key=f"callback:{farmer_token}:{payload.get('message_id', 'unknown')}", farmer_token=farmer_token, farmer_phone=profile.phone_enc, channel="voice", content={"type": "callback_request", "source": "missed_call"}, status="pending", consent_required="contact"))
    else:
        raise HTTPException(status_code=422, detail="event_type must be sms, missed_call, or ivr")
    db.commit()
    return {"status": "accepted", "farmer_token": farmer_token, "event_type": event_type}
