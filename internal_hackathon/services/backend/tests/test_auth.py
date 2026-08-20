from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.security.auth import _claim_district, _claim_role, _decode_supabase_token


def test_user_metadata_cannot_promote_a_farmer() -> None:
    assert _claim_role({"user_metadata": {"role": "admin"}, "role": "authenticated"}) == "farmer"
    assert _claim_role({"app_metadata": {"role": "extension_officer"}}) == "extension_officer"
    assert _claim_role({"user_role": "district_admin"}) == "district_admin"
    assert _claim_role({"app_metadata": {"role": "made_up_superuser"}}) == "farmer"


def test_district_is_read_from_server_controlled_metadata() -> None:
    assert _claim_district({"app_metadata": {"district_id": "nashik"}}) == "nashik"
    assert _claim_district({"district_id": "pune", "app_metadata": {"district_id": "nashik"}}) == "pune"
    assert _claim_district({"user_metadata": {"district_id": "attacker-choice"}}) is None


def test_legacy_signed_token_is_verified_with_issuer_and_safe_role(monkeypatch) -> None:
    secret = "test-only-secret-that-is-long-enough"
    supabase_url = "https://example-project.supabase.co"
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    claims = {
        "sub": "farmer-auth-subject",
        "aud": "authenticated",
        "iss": f"{supabase_url}/auth/v1",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "user_metadata": {"role": "admin"},
        "app_metadata": {"district_id": "nashik"},
    }

    context = _decode_supabase_token(jwt.encode(claims, secret, algorithm="HS256"))

    assert context.principal == "farmer-auth-subject"
    assert context.role == "farmer"
    assert context.district_id == "nashik"
