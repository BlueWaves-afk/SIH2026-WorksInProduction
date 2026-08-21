from __future__ import annotations

import httpx
import pytest

from app.adapters.whatsapp import SarvamVoiceAgentCallAdapter, WhatsAppCallAdapter, WhatsAppCloudAdapter, WhatsAppProviderError


def test_whatsapp_cloud_adapter_sends_template_message():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"messages": [{"id": "wamid.test"}]})

    adapter = WhatsAppCloudAdapter(
        access_token="wa-secret",
        phone_number_id="12345",
        graph_api_version="v20.0",
        template_name="kisansetu_support",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = adapter.send_action_card("+91 98765 43210", "whatsapp", {"band": "red", "template_parameters": ["Cotton"]})
    assert result["receipt_id"] == "wamid.test"
    assert seen["url"] == "https://graph.facebook.com/v20.0/12345/messages"
    assert seen["auth"] == "Bearer wa-secret"
    assert '"name":"kisansetu_support"' in str(seen["body"])


def test_whatsapp_call_requires_approved_partner_endpoint():
    adapter = WhatsAppCallAdapter(endpoint=None, api_key=None)
    with pytest.raises(WhatsAppProviderError, match="approved calling partner"):
        adapter.request_call("+919876543210", {"band": "red"})


def test_sarvam_voice_agent_starts_documented_outbound_attempt():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("authorization")
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"attempt_id": "attempt-123"})

    adapter = SarvamVoiceAgentCallAdapter(
        api_key="agent-secret",
        base_url="https://apps.sarvam.ai",
        org_id="org-1",
        workspace_id="workspace-1",
        app_id="kisansetu-agent",
        app_version=3,
        connection_id="connection-1",
        agent_phone_number="+918047168000",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    receipt = adapter.request_call("+919876543210", {"event_id": "event-1"})
    assert receipt == {"status": "accepted", "receipt_id": "attempt-123", "provider": "sarvam-voice-agent"}
    assert seen["url"].endswith("/api/outbounds/v1/orgs/org-1/workspaces/workspace-1/outbounds")
    assert seen["authorization"] == "Bearer agent-secret"
    assert '"user_phone_number":"+919876543210"' in seen["body"]
