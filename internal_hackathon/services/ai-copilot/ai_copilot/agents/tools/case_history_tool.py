"""AlertCase + status history fetch boundary."""


def summarize_history(history: list[dict]) -> list[str]:
    return [f"{item.get('from_status', 'new')} → {item.get('to_status')}" for item in history]
