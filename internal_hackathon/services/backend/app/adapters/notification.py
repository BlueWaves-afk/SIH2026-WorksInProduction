import structlog

logger = structlog.get_logger()

class MockNotificationAdapter:
    def send_action_card(self, farmer_phone: str, channel: str, content: dict):
        # In a real scenario, this would call SMS or Bhashini voice APIs
        logger.info(
            "Sent action card",
            phone=farmer_phone,
            channel=channel,
            content=content
        )
        return {'status': 'delivered', 'receipt_id': 'mock-12345'}

