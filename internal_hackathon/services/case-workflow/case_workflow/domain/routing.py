"""Village-to-officer routing with district fallback."""


def assign_officer(village_id: str, routes: dict[str, str], *, district_fallback: str | None = None) -> str | None:
    return routes.get(village_id) or district_fallback
