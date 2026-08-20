"""Small Supabase Auth boundary; secrets are supplied by the caller."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupabaseAuthConfig:
    url: str
    anon_key: str


class SupabaseAuthClient:
    """Lazy wrapper so importing the identity package never leaks credentials."""

    def __init__(self, config: SupabaseAuthConfig):
        self.config = config

    def session_from_access_token(self, access_token: str) -> dict[str, str]:
        if not access_token.strip():
            raise ValueError("access token is required")
        return {"access_token": access_token, "provider": "supabase"}
