"""Read-only RiskEvent + drivers fetch."""


def driver_context(event: dict) -> list[str]:
    return [str(item.get("explanation", "")) for item in event.get("contributors", [])]
