import structlog

from app.core.config import Settings
from app.adapters.whatsapp import (
    MockWhatsAppAdapter,
    SarvamVoiceAgentCallAdapter,
    WhatsAppCallAdapter,
    WhatsAppCloudAdapter,
    WhatsAppProviderError,
)
from app.integrations.email import EmailProviderError, build_email_provider

logger = structlog.get_logger()

_BAND_HEADLINE = {
    "red": "urgent support alert",
    "amber": "support advisory",
    "green": "status update",
}


def _render_email(content: dict) -> tuple[str, str]:
    """Build an identity-light subject + body from an outbox action card."""
    band = str(content.get("band", "green")).lower()
    headline = _BAND_HEADLINE.get(band, "status update")
    subject = f"KisanSetu {headline} ({band.upper()})"
    drivers = content.get("drivers") or []
    lines = [f"Your KisanSetu support status is {band.upper()}.", ""]
    reasons = [str(item.get("explanation")) for item in drivers if isinstance(item, dict) and item.get("explanation")]
    if reasons:
        lines.append("Why:")
        lines.extend(f"  - {reason}" for reason in reasons[:3])
        lines.append("")
    lines.append("An agriculture officer may follow up. You can reply STOP-style controls in the app to change how we contact you.")
    disclaimer = content.get("disclaimer")
    if disclaimer:
        lines += ["", str(disclaimer)]
    return subject, "\n".join(lines)

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
        self.email = build_email_provider(settings)
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
        # Email is orthogonal to the WhatsApp/voice provider — an opt-in farmer
        # channel routed through its own provider regardless of notify_provider.
        if channel == "email":
            return self._send_email(farmer_phone, content)
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

    def _send_email(self, destination: str, content: dict):
        subject, body = _render_email(content or {})
        try:
            result = self.email.send(to=[destination], subject=subject, text=body)
        except EmailProviderError as exc:
            raise WhatsAppProviderError(f"email delivery failed: {exc}") from exc
        return {"status": "delivered", "receipt_id": result.message_id or "email"}
