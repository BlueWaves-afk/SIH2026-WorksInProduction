"""Aggregates every v1 router (masterspec §12)."""
from fastapi import APIRouter

api_router = APIRouter()

# TODO(M1): include each router as it lands
# from app.api.v1 import farmer_profiles, observations, risk_events, mandis, \
#     cases, replay, analytics, copilot
# api_router.include_router(farmer_profiles.router, prefix="/farmer-profiles", tags=["farmer"])
# api_router.include_router(observations.router,    prefix="/observations",    tags=["signals"])
# api_router.include_router(risk_events.router,     prefix="/risk-events",     tags=["scoring"])
# api_router.include_router(mandis.router,          prefix="/mandis",          tags=["market"])
# api_router.include_router(cases.router,           prefix="/cases",           tags=["workflow"])
# api_router.include_router(replay.router,          prefix="/replay",          tags=["demo"])
# api_router.include_router(analytics.router,       prefix="/analytics",       tags=["analytics"])
# api_router.include_router(copilot.router,         prefix="/copilot",         tags=["ai"])
