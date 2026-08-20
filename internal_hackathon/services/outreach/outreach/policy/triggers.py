"""Safe outreach trigger rules."""


def should_contact(previous: str | None, current: str, *, sustained_red_days: int = 0) -> bool:
    current = current.lower()
    previous = previous.lower() if previous else None
    return current == "red" and (previous != "red" or sustained_red_days >= 3) or current == "amber" and previous != "amber" or previous is not None and previous != current and current != "green"
