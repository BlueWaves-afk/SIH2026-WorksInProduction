"""Shadow challenger boundary; it never affects the production band."""


def predict(features: dict, *, enabled: bool = False) -> dict | None:
    return {"prediction": None, "enabled": False} if not enabled else {"prediction": None, "enabled": True, "features": list(features)}
