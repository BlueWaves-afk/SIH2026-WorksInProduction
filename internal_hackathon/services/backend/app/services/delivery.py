from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.history import DeliveryAttempt
from app.models.outbox import OutboxMessage
from app.models.farmer import FarmerProfile
from app.models.risk import RiskEvent
from app.adapters.notification import MockNotificationAdapter
from app.security import decrypt_phone


def _in_quiet_hours(now: datetime) -> bool:
    hour = now.hour
    start, end = settings.quiet_hours_start, settings.quiet_hours_end
    return hour >= start or hour < end if start > end else start <= hour < end


def process_outbox(db: Session, *, now: datetime | None = None, limit: int = 50) -> dict[str, int]:
    now = now or datetime.utcnow()
    if _in_quiet_hours(now):
        return {"sent": 0, "failed": 0, "skipped_quiet_hours": 1}
    messages = (
        db.query(OutboxMessage)
        .filter(
            (OutboxMessage.status == "pending")
            | ((OutboxMessage.status == "failed") & (OutboxMessage.next_retry_at <= now))
        )
        .order_by(OutboxMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    sent = failed = 0
    adapter = MockNotificationAdapter()
    for message in messages:
        if message.idempotency_key and db.query(DeliveryAttempt).filter(DeliveryAttempt.message_id == message.message_id, DeliveryAttempt.status == "sent").first():
            message.status = "sent"
            continue
        profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == message.farmer_token).first() if message.farmer_token else None
        flags = profile.consent_flags if profile else {}
        if profile and not bool(flags.get("contact_me", flags.get("contact", False))):
            message.status = "cancelled_consent"
            db.add(DeliveryAttempt(message_id=message.message_id, channel=message.channel, status="cancelled_consent", error="contact consent withdrawn"))
            continue
        event_id = (message.content or {}).get("event_id") if isinstance(message.content, dict) else None
        if event_id:
            event = db.query(RiskEvent).filter(RiskEvent.event_id == event_id).first()
            if event and event.expires_at and event.expires_at < now:
                message.status = "suppressed_stale"
                db.add(DeliveryAttempt(message_id=message.message_id, channel=message.channel, status="suppressed_stale", error="risk event expired before delivery"))
                continue
        try:
            destination = decrypt_phone(message.farmer_phone) or message.farmer_phone
            result = adapter.send_action_card(destination, message.channel, message.content or {})
            message.status = "sent"
            message.sent_at = now
            message.error_log = None
            db.add(DeliveryAttempt(message_id=message.message_id, channel=message.channel, status="sent", provider_reference=result.get("receipt_id")))
            sent += 1
        except Exception as exc:  # pragma: no cover - provider-specific
            message.retry_count = (message.retry_count or 0) + 1
            message.status = "dead_letter" if message.retry_count >= 5 else "failed"
            message.next_retry_at = now + timedelta(minutes=15 * message.retry_count)
            message.error_log = str(exc)
            db.add(DeliveryAttempt(message_id=message.message_id, channel=message.channel, status=message.status, error=str(exc)))
            failed += 1
    db.commit()
    return {"sent": sent, "failed": failed, "skipped_quiet_hours": 0}
