"""Mock push provider (default)."""

class MockPushProvider:
    channel = "push"

    def send(self, destination: str, payload: dict) -> dict:
        return {"status": "delivered", "provider_reference": f"mock-push:{destination}", "payload": payload}

    def get_status(self, provider_reference: str) -> dict:
        return {"status": "delivered", "provider_reference": provider_reference}
