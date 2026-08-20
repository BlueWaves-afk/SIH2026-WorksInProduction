"""Case transition table shared by HTTP and worker callers."""

VALID_TRANSITIONS = {
    "new": frozenset({"acknowledged", "referred", "resolved"}),
    "acknowledged": frozenset({"visited", "referred", "resolved"}),
    "visited": frozenset({"referred", "resolved"}),
    "referred": frozenset({"visited", "resolved"}),
    "resolved": frozenset(),
}


def can_transition(current: str, target: str) -> bool:
    return target.lower() in VALID_TRANSITIONS.get(current.lower(), frozenset())


def transition(current: str, target: str) -> str:
    if not can_transition(current, target):
        raise ValueError(f"invalid transition {current} -> {target}")
    return target.lower()
