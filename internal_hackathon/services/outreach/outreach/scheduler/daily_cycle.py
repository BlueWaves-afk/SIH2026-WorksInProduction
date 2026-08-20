"""Pure daily-cycle orchestration hook."""


def run_cycle(profiles: list[dict], *, score, dispatch) -> list[dict]:
    decisions = []
    for profile in profiles:
        event = score(profile)
        result = dispatch(profile, event)
        decisions.append({"farmer_token": profile.get("farmer_token"), "event": event, "dispatch": result})
    return decisions
