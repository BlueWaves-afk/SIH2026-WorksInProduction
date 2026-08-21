"""WhatsApp Business delivery adapters.

The message adapter targets the Meta WhatsApp Cloud API shape.  A call is kept
behind a separate provider endpoint because WhatsApp calling availability is
account/region/partner gated; the platform must never pretend that a queued
call was placed when the account only has messaging access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class WhatsAppProviderError(RuntimeError):
    """A provider failure that is safe to return to the outbox worker."""


@dataclass(frozen=True)
class WhatsAppReceipt:
    provider: str
    receipt_id: str
    status: str = "accepted"


class WhatsAppCloudAdapter:
    """Send templated/text WhatsApp messages using Meta Cloud API."""

    def __init__(
        self,
        *,
        access_token: str | None,
        phone_number_id: str | None,
        graph_api_version: str = "v20.0",
        base_url: str = "https://graph.facebook.com",
        template_name: str | None = None,
        timeout_seconds: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.access_token = access_token.strip() if access_token else None
        self.phone_number_id = phone_number_id.strip() if phone_number_id else None
        self.graph_api_version = graph_api_version.strip().strip("/")
        self.base_url = base_url.rstrip("/")
        self.template_name = template_name.strip() if template_name else None
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/{self.graph_api_version}/{self.phone_number_id}/messages"

    def send_action_card(self, destination: str, channel: str, content: dict[str, Any]) -> dict[str, str]:
        if channel not in {"whatsapp", "whatsapp_message"}:
            raise WhatsAppProviderError(f"WhatsApp Cloud adapter cannot send channel {channel}")
        if not self.configured:
            raise WhatsAppProviderError("WhatsApp provider is not configured")
        recipient = _normalise_phone(destination)
        payload = _message_payload(recipient, content, template_name=self.template_name)
        response_payload = self._post(self.endpoint, payload)
        message_id = _message_id(response_payload)
        return {"status": "accepted", "receipt_id": message_id, "provider": "whatsapp-cloud"}

    def _post(self, endpoint: str, payload: dict[str, Any], *, api_key: str | None = None) -> dict[str, Any]:
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            headers = {
                "authorization": f"Bearer {api_key or self.access_token}",
                "accept": "application/json",
                "content-type": "application/json",
            }
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise WhatsAppProviderError("WhatsApp provider returned an invalid response")
            return body
        except httpx.HTTPStatusError as exc:
            raise WhatsAppProviderError(f"WhatsApp provider returned HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise WhatsAppProviderError("WhatsApp provider request failed") from exc
        finally:
            if close_client:
                client.close()


class WhatsAppCallAdapter:
    """Optional WhatsApp calling bridge for an approved Meta/telephony partner."""

    def __init__(
        self,
        *,
        endpoint: str | None,
        api_key: str | None,
        timeout_seconds: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.endpoint = endpoint.strip() if endpoint else None
        self.api_key = api_key.strip() if api_key else None
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def request_call(self, destination: str, content: dict[str, Any]) -> dict[str, str]:
        if not self.configured:
            raise WhatsAppProviderError(
                "WhatsApp calling requires an approved calling partner endpoint and credential"
            )
        recipient = _normalise_phone(destination)
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            response = client.post(
                self.endpoint or "",
                headers={"authorization": f"Bearer {self.api_key}", "accept": "application/json"},
                json={"to": recipient, "purpose": "kisansetu_support", "content": _safe_content(content)},
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            raise WhatsAppProviderError(f"WhatsApp calling provider returned HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise WhatsAppProviderError("WhatsApp calling provider request failed") from exc
        finally:
            if close_client:
                client.close()
        if not isinstance(body, dict):
            raise WhatsAppProviderError("WhatsApp calling provider returned an invalid response")
        receipt_id = str(body.get("call_id") or body.get("id") or body.get("request_id") or "")
        if not receipt_id:
            raise WhatsAppProviderError("WhatsApp calling provider returned no call reference")
        return {"status": str(body.get("status") or "accepted"), "receipt_id": receipt_id, "provider": "whatsapp-call"}


class SarvamVoiceAgentCallAdapter:
    """Start a Sarvam Voice Agents instant outbound call.

    Sarvam's documented outbound API creates a telephony attempt for a
    deployed agent.  It is intentionally kept separate from Meta's WhatsApp
    message API: voice calls on WhatsApp are account/enterprise gated, while
    Sarvam's generally available path is telephony.  The caller can therefore
    choose this adapter explicitly without misreporting a WhatsApp message as
    a call.
    """

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = "https://apps.sarvam.ai",
        org_id: str | None,
        workspace_id: str | None,
        app_id: str | None,
        app_version: int = 1,
        connection_id: str | None,
        agent_phone_number: str | None,
        timeout_seconds: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id.strip() if org_id else None
        self.workspace_id = workspace_id.strip() if workspace_id else None
        self.app_id = app_id.strip() if app_id else None
        self.app_version = app_version
        self.connection_id = connection_id.strip() if connection_id else None
        self.agent_phone_number = agent_phone_number.strip() if agent_phone_number else None
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return all(
            (
                self.api_key,
                self.org_id,
                self.workspace_id,
                self.app_id,
                self.connection_id,
                self.agent_phone_number,
            )
        )

    @property
    def endpoint(self) -> str:
        return (
            f"{self.base_url}/api/outbounds/v1/orgs/{self.org_id}"
            f"/workspaces/{self.workspace_id}/outbounds"
        )

    def request_call(self, destination: str, content: dict[str, Any] | None = None) -> dict[str, str]:
        del content  # Agent instructions/variables are configured in Sarvam Voice Agents.
        if not self.configured:
            raise WhatsAppProviderError(
                "Sarvam Voice Agents requires API key, workspace, app, connection, and agent phone settings"
            )
        recipient = _normalise_phone(destination)
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            response = client.post(
                self.endpoint,
                headers={
                    "authorization": f"Bearer {self.api_key}",
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json={
                    "app_config": {
                        "app_id": self.app_id,
                        "app_version": self.app_version,
                        "connection_config": {
                            "connection_id": self.connection_id,
                            "agent_phone_number": self.agent_phone_number,
                        },
                    },
                    "user_config": {"user_phone_number": f"+{recipient}"},
                },
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            raise WhatsAppProviderError(f"Sarvam Voice Agents returned HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise WhatsAppProviderError("Sarvam Voice Agents request failed") from exc
        finally:
            if close_client:
                client.close()
        if not isinstance(body, dict):
            raise WhatsAppProviderError("Sarvam Voice Agents returned an invalid response")
        attempt_id = str(body.get("attempt_id") or body.get("call_id") or "")
        if not attempt_id:
            raise WhatsAppProviderError("Sarvam Voice Agents returned no attempt reference")
        return {"status": "accepted", "receipt_id": attempt_id, "provider": "sarvam-voice-agent"}


class MockWhatsAppAdapter:
    """Deterministic local adapter used when a provider is not configured."""

    configured = True

    def send_action_card(self, destination: str, channel: str, content: dict[str, Any]) -> dict[str, str]:
        del destination, content
        if channel == "whatsapp_call":
            return {"status": "accepted", "receipt_id": "mock-whatsapp-call", "provider": "mock-whatsapp"}
        return {"status": "delivered", "receipt_id": "mock-whatsapp-message", "provider": "mock-whatsapp"}


def _normalise_phone(value: str) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())
    if len(digits) < 10 or len(digits) > 15:
        raise WhatsAppProviderError("destination phone must be an E.164-compatible number")
    return digits


def _message_payload(recipient: str, content: dict[str, Any], *, template_name: str | None) -> dict[str, Any]:
    chosen_template = str(content.get("template_name") or template_name or "").strip()
    if chosen_template:
        variables = content.get("template_parameters") or content.get("parameters") or []
        if not isinstance(variables, list):
            variables = []
        return {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": chosen_template,
                "language": {"code": str(content.get("language_code") or "en_US")},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": str(value)[:1024]} for value in variables],
                    }
                ]
                if variables
                else [],
            },
        }
    return {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": _render_text(content)},
    }


def _render_text(content: dict[str, Any]) -> str:
    if isinstance(content.get("text"), str) and content["text"].strip():
        return content["text"].strip()[:4096]
    band = str(content.get("band") or "support").title()
    lines = [f"KisanSetu support update: {band}"]
    for driver in content.get("drivers", [])[:3] if isinstance(content.get("drivers"), list) else []:
        if isinstance(driver, dict):
            explanation = str(driver.get("explanation") or "").strip()
            if explanation:
                lines.append(f"• {explanation[:280]}")
    disclaimer = str(content.get("disclaimer") or "This is not a credit or loan-default score.")
    lines.append(disclaimer[:280])
    return "\n".join(lines)[:4096]


def _safe_content(content: dict[str, Any]) -> dict[str, Any]:
    return {"band": content.get("band"), "event_id": content.get("event_id"), "text": _render_text(content)}


def _message_id(payload: dict[str, Any]) -> str:
    messages = payload.get("messages")
    if isinstance(messages, list) and messages and isinstance(messages[0], dict) and messages[0].get("id"):
        return str(messages[0]["id"])
    if payload.get("message_id"):
        return str(payload["message_id"])
    raise WhatsAppProviderError("WhatsApp provider returned no message reference")
