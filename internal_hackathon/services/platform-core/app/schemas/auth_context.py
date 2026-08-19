"""AuthContext — issued by M2 (identity), honoured by every module."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    FARMER = "farmer"
    EXTENSION_OFFICER = "extension_officer"
    DISTRICT_ADMIN = "district_admin"
    ADMIN = "admin"
    AUDITOR = "auditor"


class AuthContext(BaseModel):
    principal: str
    role: Role
    scopes: list[str] = Field(default_factory=list)
    mfa_verified: bool = False
    district_id: str | None = None

    def has(self, scope: str) -> bool:
        return scope in self.scopes
