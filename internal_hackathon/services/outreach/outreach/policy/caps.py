"""Per-farmer alert caps."""


def within_cap(sent_today: int, cap: int = 2) -> bool:
    return sent_today < cap
