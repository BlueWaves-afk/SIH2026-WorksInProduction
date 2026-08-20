"""Coarse profile fetch, consent-gated."""


def coarse_profile(profile: dict, *, consent_storage: bool) -> dict:
    if not consent_storage:
        raise PermissionError("storage consent is required")
    return {key: profile.get(key) for key in ("farmer_token", "village_id", "crop", "area_band", "irrigation_type")}
