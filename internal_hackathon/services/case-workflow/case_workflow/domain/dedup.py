"""Open-case-per-farmer deduplication."""


OPEN = {"new", "acknowledged", "visited", "referred"}


def deduplicate_open_cases(cases: list[dict]) -> list[dict]:
    selected: dict[str, dict] = {}
    for case in cases:
        if case.get("status", "new") not in OPEN:
            continue
        token = str(case.get("farmer_token", case.get("case_id")))
        previous = selected.get(token)
        if previous is None or (case.get("score", 0), case.get("created_at", "")) > (previous.get("score", 0), previous.get("created_at", "")):
            selected[token] = case
    return list(selected.values())
