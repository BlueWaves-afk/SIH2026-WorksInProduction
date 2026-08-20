"""Normalise inbound contact into a bounded farmer-report signal."""


def to_observation(*, farmer_token: str, report: str, source: str = "farmer") -> dict:
    return {"farmer_token": farmer_token, "source": source, "metric": "acute_farmer_report", "value": report[:280], "quality": "good"}
