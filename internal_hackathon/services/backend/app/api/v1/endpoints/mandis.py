from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.farmer import FarmerProfile
from app.models.geo import Mandi, Village
from app.models.market import MarketQuote
from app.security import AuthContext, authorize_farmer_profile, require_roles

router = APIRouter()


@router.get("/compare")
def compare_mandis(
    commodity: str = Query(default="cotton", min_length=1, max_length=64),
    farmer_token: str | None = Query(default=None, min_length=3, max_length=128),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin", "auditor")),
):
    profile = None
    if farmer_token:
        profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == farmer_token).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Farmer profile not found")
        authorize_farmer_profile(actor, profile)
    rows = (
        db.query(MarketQuote)
        .filter(MarketQuote.commodity.ilike(commodity))
        .order_by(MarketQuote.modal_price.desc(), MarketQuote.date.desc())
        .limit(limit)
        .all()
    )
    items = []
    use_geospatial = db.get_bind().dialect.name == "postgresql"
    for row in rows:
        mandi_name = row.mandi_id
        latitude = longitude = distance_km = None
        if use_geospatial:
            geo = (
                db.query(Mandi.name, func.ST_Y(Mandi.location), func.ST_X(Mandi.location))
                .filter(Mandi.mandi_id == row.mandi_id)
                .first()
            )
            if geo:
                mandi_name, latitude, longitude = geo
            if profile:
                distance_km = (
                    db.query(func.ST_DistanceSphere(Mandi.location, Village.location) / 1000.0)
                    .filter(Mandi.mandi_id == row.mandi_id, Village.village_id == profile.village_id)
                    .scalar()
                )
        items.append(
            {
                "mandi": mandi_name,
                "mandi_id": row.mandi_id,
                "commodity": row.commodity,
                "date": row.date,
                "verified_at": row.date,
                "modal_price": row.modal_price,
                "change_pct": 0.0,
                "distance_km": round(float(distance_km), 1) if distance_km is not None else 0.0,
                "latitude": float(latitude) if latitude is not None else None,
                "longitude": float(longitude) if longitude is not None else None,
                "arrivals": row.arrivals,
                "source": row.source,
                "quality": row.quality,
            }
        )
    return {
        "commodity": commodity,
        "items": items,
    }
