"""Supabase JWT verification and role/scoped access dependencies."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


@dataclass(frozen=True)
class AuthContext:
    principal: str
    role: str = "farmer"
    scopes: frozenset[str] = field(default_factory=frozenset)
    district_id: str | None = None
    mfa_verified: bool = False

    def has(self, scope: str) -> bool:
        return scope in self.scopes


APPLICATION_ROLES = frozenset({"farmer", "extension_officer", "district_admin", "admin", "auditor"})
ASYMMETRIC_ALGORITHMS = frozenset({"ES256", "RS256"})
_JWKS_TTL_SECONDS = 600
_jwks_cache: tuple[float, dict] | None = None
_jwks_lock = Lock()


def _metadata(claims: dict) -> dict:
    value = claims.get("app_metadata")
    return value if isinstance(value, dict) else {}


def _claim_role(claims: dict) -> str:
    """Read only server-controlled application role claims.

    Supabase ``user_metadata`` is user-editable and therefore never grants an
    officer or administrator role.  The built-in ``role=authenticated`` claim
    is a Postgres role, not a KisanSetu application role.
    """

    app_metadata = _metadata(claims)
    candidate = claims.get("user_role") or app_metadata.get("role")
    return str(candidate) if candidate in APPLICATION_ROLES else "farmer"


def _claim_district(claims: dict) -> str | None:
    candidate = claims.get("district_id") or _metadata(claims).get("district_id")
    return str(candidate) if candidate else None


def _jwks_endpoint() -> str:
    if settings.supabase_jwks_url:
        return settings.supabase_jwks_url
    if settings.supabase_url:
        return f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    raise HTTPException(status_code=503, detail="Supabase JWT verification is not configured")


def _load_jwks(*, force_refresh: bool = False) -> dict:
    global _jwks_cache

    now = monotonic()
    if not force_refresh and _jwks_cache and now - _jwks_cache[0] < _JWKS_TTL_SECONDS:
        return _jwks_cache[1]
    with _jwks_lock:
        now = monotonic()
        if not force_refresh and _jwks_cache and now - _jwks_cache[0] < _JWKS_TTL_SECONDS:
            return _jwks_cache[1]
        try:
            response = httpx.get(_jwks_endpoint(), timeout=5.0)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
                raise TypeError("JWKS response has no keys")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Supabase signing keys are unavailable") from exc
        _jwks_cache = (now, payload)
        return payload


def _verification_key(token: str) -> tuple[str | dict, str]:
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase token") from exc
    algorithm = header.get("alg")
    if algorithm == "HS256":
        if not settings.supabase_jwt_secret:
            raise HTTPException(status_code=503, detail="Legacy Supabase JWT verification is not configured")
        return settings.supabase_jwt_secret, algorithm
    if algorithm not in ASYMMETRIC_ALGORITHMS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported Supabase signing algorithm")
    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Supabase token has no signing key id")
    for refresh in (False, True):
        jwks = _load_jwks(force_refresh=refresh)
        match = next((key for key in jwks["keys"] if key.get("kid") == kid), None)
        if match:
            return match, algorithm
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Supabase signing key was not found")


def _decode_supabase_token(token: str) -> AuthContext:
    try:
        key, algorithm = _verification_key(token)
        issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=settings.supabase_jwt_audience,
            issuer=issuer,
        )
    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase token") from exc
    principal = claims.get("sub")
    if not principal:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has no subject")
    scopes = claims.get("scope") or claims.get("scopes") or []
    if isinstance(scopes, str):
        scopes = scopes.split()
    return AuthContext(
        principal=str(principal),
        role=_claim_role(claims),
        scopes=frozenset(str(scope) for scope in scopes),
        district_id=_claim_district(claims),
        mfa_verified=bool(claims.get("aal") in {"aal2", "mfa"}),
    )


def auth_context(
    authorization: str | None = Header(default=None),
    x_demo_role: str | None = Header(default=None),
    x_demo_principal: str | None = Header(default=None),
    x_demo_district: str | None = Header(default=None),
) -> AuthContext:
    """Resolve a principal, with an explicit local-only fixture mode.

    The demo headers are rejected whenever ``AUTH_REQUIRED`` is enabled or the
    environment is not local.  Production therefore always verifies a
    Supabase-signed JWT.
    """

    if authorization and authorization.lower().startswith("bearer "):
        return _decode_supabase_token(authorization.split(" ", 1)[1].strip())
    if settings.auth_required or settings.env.lower() not in {"local", "test"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    role = x_demo_role or "admin"
    return AuthContext(
        principal=x_demo_principal or "local-demo-user",
        role=role,
        # The implicit local admin remains convenient for integration tests,
        # while explicit demo roles exercise the same ownership/RBAC paths as
        # production JWTs instead of receiving an accidental superuser scope.
        scopes=frozenset({"*"}) if role == "admin" and not x_demo_role else frozenset(),
        district_id=x_demo_district,
        mfa_verified=True,
    )


def require_roles(*roles: str) -> Callable:
    def dependency(context: AuthContext = Depends(auth_context)) -> AuthContext:
        if "*" in context.scopes or context.role in roles:
            return context
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is not permitted")

    return dependency
