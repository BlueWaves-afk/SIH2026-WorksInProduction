from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.farmer import FarmerProfile
from app.models.observation import Observation
from app.schemas import ObservationCreate
from app.security import AuthContext, authorize_farmer_profile, require_roles
from app.security.audit import record_audit

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin")),
):
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == payload.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    authorize_farmer_profile(actor, profile)
    flags = profile.consent_flags or {}
    if not bool(flags.get("store_data", flags.get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required")
    row = Observation(
        farmer_token=payload.farmer_token,
        source=payload.source,
        observed_at=payload.observed_at.replace(tzinfo=None),
        village_id=payload.village_id or profile.village_id,
        plot_grid=payload.plot_grid,
        metric=payload.metric,
        value=payload.value,
        unit=payload.unit,
        quality=payload.quality,
        ttl=payload.ttl_seconds,
    )
    db.add(row)
    record_audit(db, actor=actor, action="observation.create", target_id=payload.farmer_token, details={"source": payload.source, "metric": payload.metric})
    db.commit()
    db.refresh(row)
    return {"id": row.id, "farmer_token": payload.farmer_token, "observation": payload.model_dump(exclude={"farmer_token"})}
