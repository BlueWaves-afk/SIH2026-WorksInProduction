"""Standard API response shapes (owned by M1, used platform-wide)."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorEnvelope(BaseModel):
    code: str = Field(..., examples=["not_found", "consent_required"])
    message: str
    request_id: str | None = None
    details: dict | None = None


class Page(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
