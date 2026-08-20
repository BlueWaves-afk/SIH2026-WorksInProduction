from fastapi import APIRouter

from app.api.v1.endpoints import analytics, cases, copilot, farmer_profiles, ingestion, mandis, notifications, observations, outreach, replay, risk_events
from app.api.v1.endpoints import consents

api_router = APIRouter()
api_router.include_router(farmer_profiles.router, prefix="/farmer-profiles", tags=["farmer-profiles"])
api_router.include_router(observations.router, prefix="/observations", tags=["observations"])
api_router.include_router(risk_events.router, prefix="/risk-events", tags=["risk-events"])
api_router.include_router(mandis.router, prefix="/mandis", tags=["mandis"])
api_router.include_router(replay.router, prefix="/replay", tags=["replay"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
api_router.include_router(consents.router, prefix="/consents", tags=["consents"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(outreach.router, prefix="/outreach", tags=["outreach"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
