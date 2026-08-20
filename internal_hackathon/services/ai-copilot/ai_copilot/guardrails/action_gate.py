"""Explicit human-approval gate for any outward-facing draft."""

from __future__ import annotations


def assert_draft_only(*, approved_by_officer: bool) -> None:
    """M7 may prepare a draft, but only M8/M6 may approve and send it."""

    if approved_by_officer:
        raise RuntimeError("M7 cannot send messages; route an approved draft through M6")
