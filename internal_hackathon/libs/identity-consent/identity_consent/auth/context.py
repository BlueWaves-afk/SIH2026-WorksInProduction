"""Provider-neutral authenticated principal contract."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthContext(BaseModel):
    principal: str
    role: str = "farmer"
    scopes: list[str] = Field(default_factory=list)
    district_id: str | None = None
    mfa_verified: bool = False

    def has(self, scope: str) -> bool:
        return "*" in self.scopes or scope in self.scopes
