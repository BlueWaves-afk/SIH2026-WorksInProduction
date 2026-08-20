"""Mock SMS provider (default)."""

class MockSMSProvider:
    channel = "sms"

    def send(self, destination: str, payload: dict) -> dict:
        return {"status": "delivered", "provider_reference": f"mock-sms:{destination[-4:]}", "payload": payload}

    def get_status(self, provider_reference: str) -> dict:
        return {"status": "delivered", "provider_reference": provider_reference}
