"""Cohort filtering for a district cycle."""


def in_scope(profiles: list[dict], *, district_id: str | None = None, village_ids: set[str] | None = None) -> list[dict]:
    return [profile for profile in profiles if (district_id is None or profile.get("district_id") == district_id) and (village_ids is None or profile.get("village_id") in village_ids)]
