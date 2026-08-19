"""CopilotBrief — produced by M7 (AI copilot), shown by M8 officer view.

Advisory only. Every scheme claim must carry a citation; the draft message
requires explicit officer approval before M6 sends anything.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_doc: str
    chunk_id: str
    quote: str


class SchemeMatch(BaseModel):
    scheme: str = Field(..., examples=["PMFBY", "PM-Kisan", "KCC"])
    why: str
    citations: list[Citation] = Field(default_factory=list)
    verified: bool = False       # only an officer sets this true


class CopilotBrief(BaseModel):
    case_id: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    scheme_matches: list[SchemeMatch] = Field(default_factory=list)
    suggested_action: str | None = None   # from the FIXED playbook enum
    draft_message: str | None = None      # requires human approval to send
    citations: list[Citation] = Field(default_factory=list)
    model_version: str | None = None
