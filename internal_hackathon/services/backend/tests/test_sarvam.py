from __future__ import annotations

import httpx

from app.integrations.sarvam import SarvamChatProvider


def test_sarvam_provider_uses_server_header_and_parses_openai_shape():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("api-subscription-key")
        body = request.read().decode("utf-8")
        seen["body"] = body
        return httpx.Response(
            200,
            json={
                "model": "sarvam-105b-conversations",
                "choices": [{"message": {"role": "assistant", "content": "Use the approved next step."}}],
            },
        )

    provider = SarvamChatProvider(
        api_key="test-secret",
        base_url="https://api.sarvam.ai/v1",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.chat([{"role": "user", "content": "What should I do?"}])

    assert result.content == "Use the approved next step."
    assert seen["url"] == "https://api.sarvam.ai/v1/chat/completions"
    assert seen["key"] == "test-secret"
    assert '"model":"sarvam-105b-conversations"' in str(seen["body"])


def test_sarvam_provider_without_key_is_safe_fallback_boundary():
    provider = SarvamChatProvider(api_key=None)
    assert provider.configured is False
