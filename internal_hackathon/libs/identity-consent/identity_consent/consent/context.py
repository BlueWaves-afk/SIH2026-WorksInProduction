"""Consent context and outward-action gate."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConsentContext(BaseModel):
    farmer_token: str
    storage: bool = False
    contact: bool = False
    analytics: bool = False
    due_window: bool = False
    consent_scopes: list[str] = Field(default_factory=list)
    version: str = "1"

    def may_contact(self) -> bool:
        return self.storage and self.contact

    def may_store(self) -> bool:
        return self.storage
