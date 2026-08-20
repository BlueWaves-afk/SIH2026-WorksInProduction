from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.farmer import FarmerProfile
from app.models.risk import RiskEvent
from app.models.geo import Village
from app.schemas import Page, RecalculateRequest, RiskEvent as RiskEventSchema
from app.security import AuthContext, authorize_farmer_profile, require_roles
from app.security.audit import record_audit
from app.integrations.live_data import LiveIngestionError, sync_profile_observations
from app.services.scoring import compute_for_profile, persist_risk_event

router = APIRouter()


def event_response(row: RiskEvent) -> RiskEventSchema:
    def aware(value: datetime | None) -> datetime | None:
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=UTC)

    return RiskEventSchema(
        event_id=row.event_id,
        farmer_token=row.farmer_token,
        village_id=row.village_id,
        score=row.score,
        band=str(row.band).lower(),
        confidence=row.confidence,
        contributors=row.contributors or [],
        action_ids=row.action_ids or [],
        model_version=row.model_version,
        evaluated_at=aware(row.evaluated_at),
        expires_at=aware(row.expires_at),
        disclaimer=row.disclaimer or "This is not a credit, loan-default, or insurance score.",
        context_flags=row.context_flags or [],
    )


@router.post("/recalculate", response_model=RiskEventSchema, status_code=status.HTTP_201_CREATED)
def recalculate_risk_event(
    payload: RecalculateRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin")),
):
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == payload.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    authorize_farmer_profile(actor, profile)
    if not bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required")
    if payload.source_mode == "live":
        try:
            sync_profile_observations(db, profile, as_of=payload.as_of)
        except LiveIngestionError as exc:
            db.rollback()
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    event = compute_for_profile(db, profile, as_of=payload.as_of)
    row = persist_risk_event(db, event)
    record_audit(db, actor=actor, action="risk_event.recalculate", target_id=event.event_id, details={"band": event.band, "score": event.score})
    db.commit()
    db.refresh(row)
    return event_response(row)


@router.get("", response_model=Page[RiskEventSchema])
def list_risk_events(
    district_id: str | None = Query(default=None),
    village_id: str | None = Query(default=None),
    farmer_token: str | None = Query(default=None),
    band: str | None = Query(default=None, pattern="^(green|amber|red)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor", "farmer")),
):
    query = db.query(RiskEvent)
    stored_tokens = [profile.farmer_token for profile in db.query(FarmerProfile).all() if bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False)))]
    query = query.filter(RiskEvent.farmer_token.in_(stored_tokens or ["__none__"]))
    if actor.district_id and district_id and actor.district_id != district_id and actor.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="Officer is not assigned to this district")
    effective_district = actor.district_id if actor.role in {"extension_officer", "district_admin"} and actor.district_id else district_id
    if effective_district:
        try:
            village_ids = [item.village_id for item in db.query(Village).filter(Village.district_id == effective_district).all()]
        except SQLAlchemyError:
            village_ids = []
        if village_ids:
            query = query.filter(RiskEvent.village_id.in_(village_ids))
        else:
            query = query.filter(RiskEvent.village_id == "__none__")
    if village_id:
        query = query.filter(RiskEvent.village_id == village_id)
    if farmer_token:
        profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == farmer_token).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Farmer profile not found")
        if not bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False))):
            raise HTTPException(status_code=403, detail="Storage consent is required")
        authorize_farmer_profile(actor, profile)
        query = query.filter(RiskEvent.farmer_token == farmer_token)
    if band:
        query = query.filter(RiskEvent.band == band)
    if actor.role == "farmer" and "*" not in actor.scopes:
        owned = db.query(FarmerProfile).filter(FarmerProfile.auth_subject == actor.principal).first()
        if not owned:
            raise HTTPException(status_code=404, detail="Farmer profile not found")
        query = query.filter(RiskEvent.farmer_token == owned.farmer_token)
    total = query.count()
    rows = query.order_by(RiskEvent.evaluated_at.desc(), RiskEvent.id.desc()).offset(offset).limit(limit).all()
    return Page[RiskEventSchema](items=[event_response(row) for row in rows], total=total, limit=limit, offset=offset)
