from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.integrations.live_data import LIVE_SOURCES, LiveIngestionError, adapter_health, fetch_live
from app.schemas import LiveIngestionPreviewRequest
from app.security import AuthContext, require_roles

router = APIRouter()


def _sources(values: list[str]) -> list[str]:
    selected = [value.strip().lower() for value in values]
    if not selected or any(value not in LIVE_SOURCES for value in selected):
        raise HTTPException(status_code=422, detail="sources must contain only imd or agmarknet")
    return list(dict.fromkeys(selected))


@router.get("/health")
def live_ingestion_health(
    _: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor")),
):
    return {
        "live_enabled": settings.live_data_enabled,
        "sources": adapter_health(),
        "contract": "ObservationPayload v1; stale rows are marked by source TTL before scoring",
    }


@router.post("/preview")
def preview_live_ingestion(
    payload: LiveIngestionPreviewRequest,
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor")),
):
    if actor.district_id and payload.district_id and actor.district_id != payload.district_id and actor.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="Officer is not assigned to this district")
    selected = _sources(payload.sources)
    try:
        result = fetch_live(
            village_id=payload.village_id,
            district_id=payload.district_id,
            mandi_id=payload.mandi_id,
            commodity=payload.commodity,
            start_date=payload.start_date,
            end_date=payload.end_date,
            sources=selected,  # type: ignore[arg-type]
        )
    except LiveIngestionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "live_enabled": settings.live_data_enabled,
        "ok": not result.errors,
        "sources": result.sources,
        "errors": result.errors,
        "observations": [item.model_dump(mode="json") for item in result.observations],
    }
