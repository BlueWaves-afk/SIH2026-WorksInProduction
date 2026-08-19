"""ConsentContext — issued by M2, gates storage, contact and analytics.

Every outward action (M6) and every profile pull (M3/AgriStack) must check this.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ConsentContext(BaseModel):
    farmer_token: str
    storage: bool = False      # may we store check-ins/profile
    contact: bool = False      # may an officer contact them
    analytics: bool = False    # may we include them in aggregate trends
    due_window: bool = False   # opt-in repayment-window signal (coarse bands only)
    consent_scopes: list[str] = Field(default_factory=list)
    version: str = "1"

    def may_contact(self) -> bool:
        return self.storage and self.contact
