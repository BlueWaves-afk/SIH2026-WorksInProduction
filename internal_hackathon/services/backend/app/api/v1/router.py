from fastapi import APIRouter
from app.api.v1.endpoints import farmer_profiles, replay, cases

api_router = APIRouter()
api_router.include_router(farmer_profiles.router, prefix='/farmer-profiles', tags=['farmer-profiles'])
api_router.include_router(replay.router, prefix='/replay', tags=['replay'])
api_router.include_router(cases.router, prefix='/cases', tags=['cases'])

