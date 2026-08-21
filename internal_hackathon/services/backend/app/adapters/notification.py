import structlog

from app.core.config import Settings
from app.adapters.whatsapp import (
    MockWhatsAppAdapter,
    SarvamVoiceAgentCallAdapter,
    WhatsAppCallAdapter,
    WhatsAppCloudAdapter,
    WhatsAppProviderError,
)

logger = structlog.get_logger()

class MockNotificationAdapter:
    def send_action_card(self, farmer_phone: str, channel: str, content: dict):
        # Compatibility facade for older callers; runtime delivery uses the
        # provider-neutral NotificationAdapter below.
        logger.info(
            "Sent action card",
            phone=farmer_phone,
            channel=channel,
            content=content
        )
        return {'status': 'delivered', 'receipt_id': 'mock-12345'}


class NotificationAdapter:
    """Provider-neutral dispatch facade used by the outbox worker."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.mock = MockWhatsAppAdapter()
        self.whatsapp = WhatsAppCloudAdapter(
            access_token=settings.whatsapp_access_token,
            phone_number_id=settings.whatsapp_phone_number_id,
            graph_api_version=settings.whatsapp_graph_api_version,
            base_url=settings.whatsapp_base_url,
            template_name=settings.whatsapp_template_name,
            timeout_seconds=settings.request_timeout_seconds,
        )
        self.call = WhatsAppCallAdapter(
            endpoint=settings.whatsapp_call_endpoint,
            api_key=settings.whatsapp_call_api_key,
            timeout_seconds=settings.request_timeout_seconds,
        )
        self.sarvam_call = SarvamVoiceAgentCallAdapter(
            api_key=settings.sarvam_voice_agent_api_key or settings.sarvam_api_key,
            base_url=settings.sarvam_voice_agent_base_url,
            org_id=settings.sarvam_voice_agent_org_id,
            workspace_id=settings.sarvam_voice_agent_workspace_id,
            app_id=settings.sarvam_voice_agent_app_id,
            app_version=settings.sarvam_voice_agent_app_version,
            connection_id=settings.sarvam_voice_agent_connection_id,
            agent_phone_number=settings.sarvam_voice_agent_phone_number,
            timeout_seconds=settings.request_timeout_seconds,
        )

    def send_action_card(self, farmer_phone: str, channel: str, content: dict):
        provider = self.settings.notify_provider.lower()
        if provider in {"mock", "fixture"}:
            return self.mock.send_action_card(farmer_phone, channel, content)
        if provider in {"whatsapp", "meta", "whatsapp_cloud"}:
            if channel == "whatsapp_call":
                if self.settings.whatsapp_call_provider.lower() == "sarvam":
                    return self.sarvam_call.request_call(farmer_phone, content)
                return self.call.request_call(farmer_phone, content)
            return self.whatsapp.send_action_card(farmer_phone, channel, content)
        raise WhatsAppProviderError(f"unsupported notification provider: {self.settings.notify_provider}")
