"""Render approved action cards without generating agronomy text."""


def render_card(card: dict, channel: str) -> dict:
    steps = [step.get("text", "") for step in card.get("steps", [])]
    return {"channel": channel, "title": card.get("title", ""), "body": " ".join(steps), "source_refs": card.get("source_refs", [])}
