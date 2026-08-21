from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.consent import ConsentLedger
from app.models.farmer import FarmerProfile as FarmerProfileRow
from app.schemas import FarmerProfile, FarmerProfileCreate
from app.security import AuthContext, encrypt_phone, new_farmer_token, require_roles
from app.security.audit import record_audit
from app.services.scoring import BOOTSTRAP_EVENT_FLAG, compute_for_profile
from app.services.workflow import persist_event_with_workflow

router = APIRouter()


@router.get("/me", response_model=FarmerProfile)
def get_my_farmer_profile(
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer")),
):
    profile = db.query(FarmerProfileRow).filter(FarmerProfileRow.auth_subject == actor.principal).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return profile


@router.post("", response_model=FarmerProfile, status_code=status.HTTP_201_CREATED)
def create_farmer_profile(
    profile: FarmerProfileCreate,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin")),
):
    farmer_token = profile.farmer_token or new_farmer_token()
    if actor.role == "farmer" and db.query(FarmerProfileRow).filter(FarmerProfileRow.auth_subject == actor.principal).first():
        raise HTTPException(status_code=409, detail="Authenticated farmer already has a profile")
    if db.query(FarmerProfileRow).filter(FarmerProfileRow.farmer_token == farmer_token).first():
        raise HTTPException(status_code=409, detail="Farmer profile already exists")
    flags = profile.consent_flags.model_dump()
    db_profile = FarmerProfileRow(
        farmer_token=farmer_token,
        auth_subject=actor.principal if actor.role == "farmer" else None,
        village_id=profile.village_id,
        locale=profile.locale,
        crop=profile.crop,
        sowing_date=profile.sowing_date,
        irrigation_type=profile.irrigation_type,
        area_band=profile.area_band,
        phone_enc=encrypt_phone(profile.phone),
        consent_flags=flags,
        secondary_crop=profile.secondary_crop,
        schemes_enrolled=profile.schemes_enrolled,
        institutional_access=profile.institutional_access,
        soil_retention=profile.soil_retention,
    )
    db.add(db_profile)
    for purpose, enabled in flags.items():
        db.add(
            ConsentLedger(
                farmer_token=farmer_token,
                action="GRANT" if enabled else "WITHDRAW",
                purpose=purpose,
                proof={"version": "1", "actor": actor.principal},
            )
        )
    # Bootstrap the first, conservative status in the same transaction as the
    # profile. The farmer home screen reads RiskEvent immediately after setup;
    # without this empty-observation score, a valid new profile has no status
    # row and the UI can only report "No saved status is available". Missing
    # signals intentionally produce a green, low-confidence event with the
    # scorer's suppression flag rather than fabricated risk.
    db.flush()
    initial_event = compute_for_profile(db, db_profile, rows=[])
    initial_event.context_flags = [*initial_event.context_flags, BOOTSTRAP_EVENT_FLAG]
    persist_event_with_workflow(db, db_profile, initial_event, actor=actor)
    record_audit(db, actor=actor, action="farmer_profile.create", target_id=farmer_token, details={"village_id": profile.village_id})
    db.commit()
    db.refresh(db_profile)
    return db_profile
