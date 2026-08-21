from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import AlertCase
from app.models.consent import ConsentLedger
from app.models.farmer import FarmerProfile
from app.models.history import CaseStatusHistory, DeliveryAttempt
from app.models.observation import Observation
from app.models.outbox import OutboxMessage
from app.models.risk import RiskEvent
from app.schemas import ConsentUpdate
from app.security import AuthContext, authorize_farmer_profile, require_roles
from app.security.audit import record_audit

router = APIRouter()


def _profile_or_404(token: str, db: Session) -> FarmerProfile:
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return profile


@router.get("/{farmer_token}")
def get_consent(farmer_token: str, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin", "auditor"))):
    profile = _profile_or_404(farmer_token, db)
    authorize_farmer_profile(actor, profile)
    return {"farmer_token": farmer_token, "consent": profile.consent_flags or {}}


@router.put("/{farmer_token}")
def update_consent(
    farmer_token: str,
    payload: ConsentUpdate,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin")),
):
    profile = _profile_or_404(farmer_token, db)
    authorize_farmer_profile(actor, profile)
    flags = dict(profile.consent_flags or {})
    requested = payload.model_dump(exclude_none=True, exclude={"version"})
    aliases = {"storage": "store_data", "contact": "contact_me", "whatsapp_call": "whatsapp_call", "analytics": "use_analytics", "due_window": "due_window"}
    changed = {aliases[key]: value for key, value in requested.items()}
    for key, value in changed.items():
        flags[key] = value
        # Keep the HTTP aliases out of the persisted source of truth; all
        # scoring, delivery, and deletion paths read these canonical keys.
        db.add(ConsentLedger(farmer_token=farmer_token, action="GRANT" if value else "WITHDRAW", purpose=key, proof={"version": payload.version, "actor": actor.principal}))
    profile.consent_flags = flags
    record_audit(db, actor=actor, action="consent.update", target_id=farmer_token, details={"changed": list(changed)})
    db.commit()
    return {"farmer_token": farmer_token, "consent": flags, "version": payload.version}


@router.get("/{farmer_token}/export")
def export_farmer_data(farmer_token: str, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin", "auditor"))):
    profile = _profile_or_404(farmer_token, db)
    authorize_farmer_profile(actor, profile)
    return {
        "profile": {"farmer_token": profile.farmer_token, "village_id": profile.village_id, "locale": profile.locale, "crop": profile.crop, "consent_flags": profile.consent_flags},
        "observations": [{"source": row.source, "metric": row.metric, "observed_at": row.observed_at, "value": row.value, "quality": row.quality} for row in db.query(Observation).filter(Observation.farmer_token == farmer_token).all()],
        "risk_events": [{"event_id": row.event_id, "score": row.score, "band": row.band, "evaluated_at": row.evaluated_at} for row in db.query(RiskEvent).filter(RiskEvent.farmer_token == farmer_token).all()],
        "cases": [{"case_id": row.id, "event_id": row.event_id, "status": row.status, "resolution_code": row.resolution_code, "notes": row.notes} for row in db.query(AlertCase).filter(AlertCase.farmer_token == farmer_token).all()],
    }


@router.delete("/{farmer_token}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farmer_data(farmer_token: str, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("farmer", "district_admin", "admin"))):
    profile = _profile_or_404(farmer_token, db)
    authorize_farmer_profile(actor, profile)
    db.query(Observation).filter(Observation.farmer_token == farmer_token).delete(synchronize_session=False)
    db.query(RiskEvent).filter(RiskEvent.farmer_token == farmer_token).delete(synchronize_session=False)
    case_ids = [row.id for row in db.query(AlertCase.id).filter(AlertCase.farmer_token == farmer_token).all()]
    if case_ids:
        db.query(CaseStatusHistory).filter(CaseStatusHistory.case_id.in_(case_ids)).delete(synchronize_session=False)
    db.query(AlertCase).filter(AlertCase.farmer_token == farmer_token).delete(synchronize_session=False)
    message_ids = [row.message_id for row in db.query(OutboxMessage.message_id).filter(OutboxMessage.farmer_token == farmer_token).all()]
    if message_ids:
        db.query(DeliveryAttempt).filter(DeliveryAttempt.message_id.in_(message_ids)).delete(synchronize_session=False)
    db.query(OutboxMessage).filter(OutboxMessage.farmer_token == farmer_token).delete(synchronize_session=False)
    db.delete(profile)
    record_audit(db, actor=actor, action="data.delete", target_id=farmer_token, details={"retained": "audit event"})
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
