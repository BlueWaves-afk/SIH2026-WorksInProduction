from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.farmer import FarmerProfile
from app.schemas import ReplayRequest
from app.security import AuthContext, require_roles
from app.security.audit import record_audit
from app.services.replay import run_replay
from app.api.v1.endpoints.risk_events import event_response

router = APIRouter()


@router.post("/scenario")
def replay_scenario(
    request: ReplayRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor")),
):
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == request.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if not bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required for replay")
    result = run_replay(db, profile, request.scenario, request.day_offset)
    record_audit(db, actor=actor, action="replay.run", target_id=result["event"].event_id, details={"scenario": result["scenario"]})
    db.commit()
    return {
        'farmer_token': profile.farmer_token,
        'scenario': request.scenario,
        'risk_event': event_response(result['event_row']),
        'case': ({'case_id': result['case_row'].id, 'status': result['case_row'].status} if result['case_row'] else None),
    }
