from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import AlertCase as AlertCaseRow
from app.models.farmer import FarmerProfile
from app.models.history import CaseStatusHistory
from app.schemas import AlertCase, CaseResolveRequest, CaseStatus, CaseTransitionRequest, Page
from app.security import AuthContext, require_roles
from app.security.audit import record_audit
from app.models.geo import Village

router = APIRouter()


ALLOWED_TRANSITIONS = {
    "new": {"acknowledged", "referred", "resolved"},
    "acknowledged": {"visited", "referred", "resolved"},
    "visited": {"referred", "resolved"},
    "referred": {"visited", "resolved"},
    "resolved": set(),
}
RESOLUTION_CODES = {"supported", "referred", "visited", "unable_to_reach", "false_positive", "duplicate"}


def _authorize_case(case: AlertCaseRow, actor: AuthContext, db: Session) -> None:
    if actor.role == "extension_officer" and case.assigned_to and case.assigned_to != actor.principal:
        raise HTTPException(status_code=403, detail="Case is assigned to another officer")
    if actor.district_id:
        try:
            allowed = db.query(Village).filter(Village.village_id == case.village_id, Village.district_id == actor.district_id).first()
        except SQLAlchemyError:
            allowed = None
        if not allowed:
            raise HTTPException(status_code=403, detail="Case is outside the officer's district")


def _case_response(case: AlertCaseRow) -> AlertCase:
    return AlertCase(
        case_id=str(case.id),
        event_id=case.event_id,
        farmer_token=case.farmer_token or "",
        village_id=case.village_id or "",
        recipient_role=case.recipient_role or "extension_officer",
        band=str(case.band or "amber").lower(),
        confidence=float(case.confidence or 0),
        assigned_to=case.assigned_to,
        status=str(case.status or "new").lower(),
        sent_at=case.sent_at,
        ack_at=case.ack_at,
        sla_due_at=case.sla_due_at,
        resolution_code=case.resolution_code,
        notes=case.notes,
    )


def _transition(case: AlertCaseRow, target: str, actor: AuthContext, db: Session, *, reason: str | None = None, notes: str | None = None) -> None:
    current = str(case.status or "new").lower()
    target = target.lower()
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(status_code=409, detail=f"Invalid case transition {current} -> {target}")
    db.add(CaseStatusHistory(case_id=case.id, from_status=current, to_status=target, actor_id=actor.principal, reason=reason, details={"notes": notes} if notes else {}))
    case.status = target
    case.updated_at = datetime.utcnow()
    if target == "acknowledged":
        case.ack_at = datetime.utcnow()
        case.assigned_to = case.assigned_to or actor.principal
    if notes:
        case.notes = notes
    record_audit(db, actor=actor, action=f"case.{target}", target_id=str(case.id), details={"from": current, "reason": reason})


@router.get("", response_model=Page[AlertCase])
def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    band: str | None = Query(default=None, pattern="^(green|amber|red)$"),
    district_id: str | None = Query(default=None),
    village_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor")),
):
    query = db.query(AlertCaseRow)
    stored_tokens = [profile.farmer_token for profile in db.query(FarmerProfile).all() if bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False)))]
    query = query.filter(AlertCaseRow.farmer_token.in_(stored_tokens or ["__none__"]))
    if status_filter:
        query = query.filter(AlertCaseRow.status == status_filter.lower())
    if band:
        query = query.filter(AlertCaseRow.band == band)
    if actor.district_id and district_id and actor.district_id != district_id and actor.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="Officer is not assigned to this district")
    effective_district = actor.district_id if actor.role in {"extension_officer", "district_admin"} and actor.district_id else district_id
    if village_id:
        query = query.filter(AlertCaseRow.village_id == village_id)
    if effective_district:
        try:
            village_ids = [item.village_id for item in db.query(Village).filter(Village.district_id == effective_district).all()]
        except SQLAlchemyError:
            village_ids = []
        query = query.filter(AlertCaseRow.village_id.in_(village_ids or ["__none__"]))
    if actor.role == "extension_officer":
        # Unassigned cases remain visible so the first officer who acknowledges
        # them becomes the owner; assigned cases are private to that officer.
        query = query.filter(or_(AlertCaseRow.assigned_to.is_(None), AlertCaseRow.assigned_to == actor.principal))
    total = query.count()
    rows = query.order_by(AlertCaseRow.sla_due_at.asc(), AlertCaseRow.created_at.desc()).offset(offset).limit(limit).all()
    return Page[AlertCase](items=[_case_response(row) for row in rows], total=total, limit=limit, offset=offset)


@router.post("/{case_id}/acknowledge", response_model=AlertCase)
def acknowledge_case(case_id: int, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin"))):
    case = db.query(AlertCaseRow).filter(AlertCaseRow.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    _authorize_case(case, actor, db)
    _transition(case, CaseStatus.ACKNOWLEDGED.value, actor, db)
    db.commit()
    db.refresh(case)
    return _case_response(case)


@router.post("/{case_id}/resolve", response_model=AlertCase)
def resolve_case(case_id: int, payload: CaseResolveRequest, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin"))):
    case = db.query(AlertCaseRow).filter(AlertCaseRow.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    _authorize_case(case, actor, db)
    if payload.resolution_code not in RESOLUTION_CODES:
        raise HTTPException(status_code=422, detail=f"resolution_code must be one of {sorted(RESOLUTION_CODES)}")
    _transition(case, CaseStatus.RESOLVED.value, actor, db, reason=payload.resolution_code, notes=payload.notes)
    case.resolution_code = payload.resolution_code
    db.commit()
    db.refresh(case)
    return _case_response(case)


@router.post("/{case_id}/transition", response_model=AlertCase)
def transition_case(case_id: int, payload: CaseTransitionRequest, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin"))):
    case = db.query(AlertCaseRow).filter(AlertCaseRow.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    _authorize_case(case, actor, db)
    _transition(case, payload.status.value, actor, db, reason=payload.reason, notes=payload.notes)
    db.commit()
    db.refresh(case)
    return _case_response(case)


@router.post("/{case_id}/reopen", response_model=AlertCase)
def reopen_case(case_id: int, payload: CaseTransitionRequest | None = None, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin"))):
    case = db.query(AlertCaseRow).filter(AlertCaseRow.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    _authorize_case(case, actor, db)
    if str(case.status).lower() != "resolved":
        raise HTTPException(status_code=409, detail="Only resolved cases can be reopened")
    case.status = "acknowledged"
    case.resolution_code = None
    case.updated_at = datetime.utcnow()
    case.assigned_to = case.assigned_to or actor.principal
    db.add(CaseStatusHistory(case_id=case.id, from_status="resolved", to_status="acknowledged", actor_id=actor.principal, reason=(payload.reason if payload else "reopened"), details={"policy": "manual_reopen"}))
    record_audit(db, actor=actor, action="case.reopen", target_id=str(case.id), details={"policy": "manual_reopen"})
    db.commit()
    db.refresh(case)
    return _case_response(case)


@router.get("/{case_id}/history")
def case_history(case_id: int, db: Session = Depends(get_db), actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor"))):
    case = db.query(AlertCaseRow).filter(AlertCaseRow.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    _authorize_case(case, actor, db)
    rows = db.query(CaseStatusHistory).filter(CaseStatusHistory.case_id == case_id).order_by(CaseStatusHistory.created_at.asc()).all()
    return {"case_id": case_id, "items": [{"from_status": row.from_status, "to_status": row.to_status, "actor_id": row.actor_id, "reason": row.reason, "details": row.details or {}, "created_at": row.created_at} for row in rows]}
