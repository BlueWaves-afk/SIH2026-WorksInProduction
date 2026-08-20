from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.integrations.canonical import ReplayDriver
from app.models.case import AlertCase
from app.models.farmer import FarmerProfile
from app.models.observation import Observation
from app.models.outbox import OutboxMessage
from app.services.scoring import compute_for_profile, persist_risk_event


SCENARIO_ALIASES = {
    "drought": "rainfall_shock",
    "drought_crash": "rainfall_shock",
}


def run_replay(db: Session, profile: FarmerProfile, scenario: str, day_offset: int = 0) -> dict:
    canonical_scenario = SCENARIO_ALIASES.get(scenario, scenario)
    bundle = ReplayDriver().generate(canonical_scenario, day_offset)
    rows: list[Observation] = []
    for payload in bundle.observations:
        row = Observation(
            farmer_token=profile.farmer_token,
            source=payload.source,
            observed_at=payload.observed_at.replace(tzinfo=None),
            village_id=profile.village_id,
            plot_grid=payload.plot_grid,
            metric=payload.metric,
            value=payload.value,
            unit=payload.unit,
            quality=payload.quality,
            ttl=int(payload.ttl.total_seconds()),
        )
        db.add(row)
        rows.append(row)
    db.flush()
    as_of = datetime(2026, 6, 1, tzinfo=UTC) + timedelta(days=day_offset)
    event = compute_for_profile(db, profile, as_of=as_of, rows=rows)
    event_row = persist_risk_event(db, event)
    case_row = None
    if event.band in {"amber", "red"} and "escalation suppressed: low confidence" not in event.context_flags:
        recent_open = (
            db.query(AlertCase)
            .filter(AlertCase.farmer_token == profile.farmer_token, AlertCase.status.in_(["new", "acknowledged", "visited", "referred"]), AlertCase.band == event.band)
            .order_by(AlertCase.created_at.desc())
            .first()
        )
        if recent_open and recent_open.created_at and datetime.utcnow() - recent_open.created_at < timedelta(hours=24):
            case_row = recent_open
        else:
            case_row = AlertCase(
                event_id=event.event_id,
                farmer_token=profile.farmer_token,
                village_id=profile.village_id,
                recipient_role="extension_officer",
                channel="sms",
                sent_at=datetime.utcnow(),
                status="new",
                band=event.band,
                confidence=event.confidence,
                sla_due_at=datetime.utcnow() + timedelta(hours=24 if event.band == "amber" else 8),
            )
            db.add(case_row)
            db.flush()
        flags = profile.consent_flags or {}
        may_contact = bool(flags.get("contact_me", flags.get("contact", False))) and bool(
            flags.get("store_data", flags.get("storage", False))
        )
        if may_contact and (case_row.event_id == event.event_id):
            db.add(
                OutboxMessage(
                    message_id=str(uuid4()),
                    idempotency_key=f"risk:{event.event_id}:contact",
                    farmer_token=profile.farmer_token,
                    farmer_phone=profile.phone_enc,
                    channel="sms",
                    content={"event_id": event.event_id, "band": event.band, "drivers": [item.model_dump(mode="json") for item in event.contributors]},
                    status="pending",
                    consent_required="contact",
                )
            )
    db.commit()
    return {"event": event, "event_row": event_row, "case_row": case_row, "scenario": canonical_scenario}
