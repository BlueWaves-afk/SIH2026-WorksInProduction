"""Turn a missed call into a callback request without exposing the number."""


def callback_request(farmer_token: str) -> dict:
    return {"farmer_token": farmer_token, "type": "callback_request", "status": "queued"}
