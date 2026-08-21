"""Durable score -> case -> notification orchestration.

Every scoring entry point (replay, live recalculation, and future scheduled
refreshes) uses this service.  Keeping the side effects here prevents one path
from silently bypassing deduplication, case history, consent, or outbox
idempotency.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.case import AlertCase
from app.models.farmer import FarmerProfile
from app.models.history import CaseStatusHistory
from app.models.outbox import OutboxMessage
from app.security import AuthContext
from app.security.audit import record_audit
from app.services.scoring import persist_risk_event


OPEN_STATUSES = ("new", "acknowledged", "visited", "referred")


def persist_event_with_workflow(
    db: Session,
    profile: FarmerProfile,
    event,
    *,
    actor: AuthContext | None = None,
    now: datetime | None = None,
) -> tuple[object, AlertCase | None]:
    """Persist a RiskEvent and idempotently project it into M5/M6 records."""

    now = now or datetime.utcnow()
    actor = actor or AuthContext(principal="scoring-service", role="admin", scopes=frozenset({"*"}))
    event_row = persist_risk_event(db, event)
    case_row: AlertCase | None = None

    if event.band in {"amber", "red"} and "escalation suppressed: low confidence" not in event.context_flags:
        case_row = (
            db.query(AlertCase)
            .filter(AlertCase.farmer_token == profile.farmer_token, AlertCase.status.in_(OPEN_STATUSES))
            .order_by(AlertCase.updated_at.desc(), AlertCase.id.desc())
            .first()
        )
        previous_band = str(case_row.band).lower() if case_row and case_row.band else None
        created = case_row is None
        if created:
            case_row = AlertCase(
                event_id=event.event_id,
                farmer_token=profile.farmer_token,
                village_id=profile.village_id,
                recipient_role="extension_officer",
                channel="whatsapp",
                sent_at=now,
                status="new",
                band=event.band,
                confidence=event.confidence,
                sla_due_at=now + timedelta(hours=24 if event.band == "amber" else 8),
            )
            db.add(case_row)
            db.flush()
            db.add(CaseStatusHistory(case_id=case_row.id, from_status=None, to_status="new", actor_id=actor.principal, reason="risk_event_created", details={"event_id": event.event_id}))
        else:
            case_row.event_id = event.event_id
            case_row.band = event.band
            case_row.confidence = event.confidence
            case_row.village_id = profile.village_id
            case_row.updated_at = now
            db.add(CaseStatusHistory(case_id=case_row.id, from_status=case_row.status, to_status=case_row.status, actor_id=actor.principal, reason="risk_event_updated", details={"event_id": event.event_id, "previous_band": previous_band}))

        flags = profile.consent_flags or {}
        may_contact = bool(flags.get("contact_me", flags.get("contact", False))) and bool(flags.get("store_data", flags.get("storage", False)))
        band_changed = previous_band is not None and previous_band != event.band
        if may_contact and (created or band_changed):
            idem = f"risk:{event.event_id}:contact"
            if db.query(OutboxMessage).filter(OutboxMessage.idempotency_key == idem).first() is None:
                db.add(OutboxMessage(
                    message_id=str(uuid4()),
                    idempotency_key=idem,
                    farmer_token=profile.farmer_token,
                    farmer_phone=profile.phone_enc,
                    channel="whatsapp",
                    content={"event_id": event.event_id, "band": event.band, "drivers": [item.model_dump(mode="json") for item in event.contributors], "expires_at": event.expires_at.isoformat()},
                    status="pending",
                    consent_required="contact",
                ))

    record_audit(db, actor=actor, action="risk_event.project", target_id=event.event_id, details={"band": event.band, "score": event.score, "case_id": case_row.id if case_row else None})
    return event_row, case_row


__all__ = ["persist_event_with_workflow"]
