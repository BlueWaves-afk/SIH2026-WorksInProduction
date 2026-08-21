"""Consent-aware band-change and sustained-Red outreach orchestration."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.farmer import FarmerProfile
from app.models.outbox import OutboxMessage
from app.models.risk import RiskEvent
from app.security import AuthContext
from app.security.audit import record_audit


def _quiet(now: datetime) -> bool:
    start, end = settings.quiet_hours_start, settings.quiet_hours_end
    return now.hour >= start or now.hour < end if start > end else start <= now.hour < end


def _select_channel(band: str, flags: dict) -> str | None:
    if not flags.get("contact_me", flags.get("contact", False)):
        return None
    if band == "red":
        # WhatsApp messaging is the default farmer channel.  A live call is
        # requested only when explicitly enabled and is handled by an
        # approved WhatsApp/telephony partner, never assumed to exist.
        return "whatsapp_call" if flags.get("whatsapp_call", False) else "whatsapp"
    return "whatsapp"


def _should_contact(previous: str | None, current: str, red_count: int) -> bool:
    if current == "red":
        return previous != "red" or red_count >= 3
    if current == "amber":
        return previous != "amber"
    return previous is not None and previous != current and current != "green"


def run_outreach_cycle(db: Session, *, now: datetime | None = None, actor: AuthContext | None = None) -> dict:
    """Create at most one consented, idempotent outbox message per event.

    This is deliberately a decision pass: provider delivery remains in the
    outbox worker, so quiet hours, retries, caps, and dead letters are all
    observable and auditable.
    """

    now = now or datetime.utcnow()
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    system_actor = actor or AuthContext(principal="outreach-scheduler", role="admin", scopes=frozenset({"*"}))
    created = skipped = 0
    decisions: list[dict] = []
    profiles = db.query(FarmerProfile).all()
    for profile in profiles:
        events = (
            db.query(RiskEvent)
            .filter(RiskEvent.farmer_token == profile.farmer_token)
            .order_by(RiskEvent.evaluated_at.desc(), RiskEvent.id.desc())
            .limit(10)
            .all()
        )
        if not events:
            continue
        current = events[0]
        previous = str(events[1].band).lower() if len(events) > 1 else None
        red_count = sum(1 for item in events if str(item.band).lower() == "red" and item.evaluated_at and now - item.evaluated_at.replace(tzinfo=None) <= timedelta(days=3))
        flags = profile.consent_flags or {}
        reason = "band_change_or_sustained_red"
        if "escalation suppressed: low confidence" in (current.context_flags or []):
            reason = "low_confidence_suppressed"
            skipped += 1
            decisions.append({"farmer_token": profile.farmer_token, "status": "suppressed", "reason": reason})
            continue
        if not _should_contact(previous, str(current.band).lower(), red_count):
            skipped += 1
            decisions.append({"farmer_token": profile.farmer_token, "status": "not_triggered", "reason": "no_band_change"})
            continue
        if not flags.get("store_data", flags.get("storage", False)):
            skipped += 1
            decisions.append({"farmer_token": profile.farmer_token, "status": "blocked", "reason": "storage_consent"})
            continue
        channel = _select_channel(str(current.band).lower(), flags)
        if not channel:
            skipped += 1
            decisions.append({"farmer_token": profile.farmer_token, "status": "blocked", "reason": "contact_consent"})
            continue
        if _quiet(now) and channel == "whatsapp_call":
            channel = "whatsapp"  # quiet-hours ladder; message is queued instead
        day_start = datetime.combine(now.date(), time.min)
        sent_today = db.query(OutboxMessage).filter(OutboxMessage.farmer_token == profile.farmer_token, OutboxMessage.created_at >= day_start).count()
        if sent_today >= settings.outreach_daily_cap:
            skipped += 1
            decisions.append({"farmer_token": profile.farmer_token, "status": "capped", "reason": "daily_cap"})
            continue
        idem = f"outreach:{current.event_id}:{channel}"
        if db.query(OutboxMessage).filter(OutboxMessage.idempotency_key == idem).first():
            skipped += 1
            decisions.append({"farmer_token": profile.farmer_token, "status": "duplicate", "reason": "idempotency"})
            continue
        message = OutboxMessage(
            message_id=str(uuid4()),
            idempotency_key=idem,
            farmer_token=profile.farmer_token,
            farmer_phone=profile.phone_enc,
            channel=channel,
            content={
                "event_id": current.event_id,
                "band": str(current.band).lower(),
                "drivers": current.contributors or [],
                "disclaimer": current.disclaimer,
                "reason": reason,
            },
            status="pending",
            consent_required="whatsapp_call" if channel == "whatsapp_call" else "contact",
        )
        db.add(message)
        record_audit(db, actor=system_actor, action="outreach.decision", target_id=profile.farmer_token, details={"event_id": current.event_id, "channel": channel, "reason": reason})
        decisions.append({"farmer_token": profile.farmer_token, "status": "queued", "channel": channel, "event_id": current.event_id})
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "decisions": decisions}
