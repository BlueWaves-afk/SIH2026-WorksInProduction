"""Fixed, auditable action playbook. The model may select, never invent."""

from __future__ import annotations

from enum import StrEnum

from app.schemas import Band


class PlaybookAction(StrEnum):
    CALL_FARMER = "CALL_FARMER"
    SEND_ADVISORY = "SEND_ADVISORY"
    REFER_FPO = "REFER_FPO"
    REFER_KVK = "REFER_KVK"
    SCHEDULE_VISIT = "SCHEDULE_VISIT"
    RESOLVE_FALSE_POSITIVE = "RESOLVE_FALSE_POSITIVE"
    ESCALATE_DISTRICT = "ESCALATE_DISTRICT"


def choose_playbook_action(*, band: Band, drivers: list[str]) -> PlaybookAction:
    lowered = " ".join(drivers).lower()
    if band is Band.RED and "price" in lowered:
        return PlaybookAction.REFER_FPO
    if band is Band.RED:
        return PlaybookAction.SCHEDULE_VISIT
    if band is Band.AMBER:
        return PlaybookAction.SEND_ADVISORY
    return PlaybookAction.RESOLVE_FALSE_POSITIVE
