from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case as sql_case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.case import AlertCase
from app.models.farmer import FarmerProfile
from app.models.risk import RiskEvent
from app.security import AuthContext, require_roles

router = APIRouter()


@router.get("/district")
def district_analytics(
    district_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor")),
):
    # District filtering is applied by village in deployments that populate the
    # geography table.  The demo fallback still returns useful global metrics.
    events = db.query(RiskEvent)
    cases = db.query(AlertCase)
    stored_tokens = [profile.farmer_token for profile in db.query(FarmerProfile).all() if bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False)))]
    events = events.filter(RiskEvent.farmer_token.in_(stored_tokens or ["__none__"]))
    cases = cases.filter(AlertCase.farmer_token.in_(stored_tokens or ["__none__"]))
    effective_district = actor.district_id if actor.role in {"extension_officer", "district_admin"} and actor.district_id else district_id
    if actor.district_id and district_id and actor.district_id != district_id and actor.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="Officer is not assigned to this district")
    village_ids: list[str] = []
    if effective_district:
        from app.models.geo import Village

        try:
            village_ids = [item.village_id for item in db.query(Village).filter(Village.district_id == effective_district).all()]
        except SQLAlchemyError:
            village_ids = []
        events = events.filter(RiskEvent.village_id.in_(village_ids or ["__none__"]))
        cases = cases.filter(AlertCase.village_id.in_(village_ids or ["__none__"]))
    hotspot_rows = (
        cases.with_entities(
            AlertCase.village_id,
            func.count(AlertCase.id),
            func.sum(sql_case((AlertCase.band == "red", 1), else_=0)),
        )
        .filter(AlertCase.status != "resolved")
        .group_by(AlertCase.village_id)
        .all()
    )
    hotspots = []
    for village_id, open_count, red_count in hotspot_rows:
        latitude = longitude = None
        if db.get_bind().dialect.name == "postgresql":
            from app.models.geo import Village

            point = (
                db.query(func.ST_Y(Village.location), func.ST_X(Village.location))
                .filter(Village.village_id == village_id)
                .first()
            )
            if point:
                latitude, longitude = point
        hotspots.append(
            {
                "village_id": village_id,
                "open_cases": int(open_count or 0),
                "red_cases": int(red_count or 0),
                "latitude": float(latitude) if latitude is not None else None,
                "longitude": float(longitude) if longitude is not None else None,
                "precision": "village_centroid",
            }
        )
    return {
        "district_id": effective_district,
        "risk_events": events.count(),
        "red_events": events.filter(RiskEvent.band == "red").count(),
        "amber_events": events.filter(RiskEvent.band == "amber").count(),
        "open_cases": cases.filter(AlertCase.status.in_(["new", "acknowledged", "visited", "referred"])).count(),
        "resolved_cases": cases.filter(AlertCase.status == "resolved").count(),
        "hotspots": hotspots,
    }
