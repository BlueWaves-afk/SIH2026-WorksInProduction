"""Farmer resource ownership checks.

``farmer_token`` deliberately remains an opaque resource identifier.  Access
is granted by the Supabase JWT subject persisted on the farmer profile, never
by possession of the token itself.
"""

from __future__ import annotations

import secrets

from fastapi import HTTPException

from app.core.config import settings
from app.models.farmer import FarmerProfile
from app.security.auth import AuthContext


def authorize_farmer_profile(actor: AuthContext, profile: FarmerProfile) -> None:
    if actor.role != "farmer" or "*" in actor.scopes:
        return
    if settings.env.lower() in {"local", "test"} and actor.principal == "local-demo-user":
        return
    owner = profile.auth_subject or ""
    if not owner or not secrets.compare_digest(owner, actor.principal):
        raise HTTPException(status_code=403, detail="Farmer may only access their own record")
