"""Server-side Sarvam chat provider.

The browser never receives the Sarvam subscription key.  This adapter speaks
Sarvam's OpenAI-compatible chat-completions contract and deliberately exposes
only the small surface needed by the bounded farmer-support agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class SarvamProviderError(RuntimeError):
    """A provider failure that is safe to surface as a deterministic fallback."""


@dataclass(frozen=True)
class SarvamChatResult:
    content: str
    model: str
    provider: str = "sarvam"


class SarvamChatProvider:
    """Minimal, testable Sarvam chat-completions client.

    ``api_key`` is accepted only by this server-side class and is never
    included in an exception, log message, or response model.
    """

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = "https://api.sarvam.ai/v1",
        model: str = "sarvam-105b-conversations",
        timeout_seconds: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 256,
    ) -> SarvamChatResult:
        if not self.configured:
            raise SarvamProviderError("Sarvam provider is not configured")
        if not messages:
            raise SarvamProviderError("Sarvam request has no messages")

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        headers = {
            "api-subscription-key": self.api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            try:
                response = client.post(self.endpoint, headers=headers, json=body)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as exc:
                raise SarvamProviderError(f"Sarvam request failed with HTTP {exc.response.status_code}") from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise SarvamProviderError("Sarvam request failed") from exc
        finally:
            if close_client:
                client.close()

        content = _extract_content(payload)
        if not content:
            raise SarvamProviderError("Sarvam response did not contain assistant content")
        return SarvamChatResult(content=content, model=str(payload.get("model") or self.model))


def _extract_content(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        # Accept the common content-part shape but only keep text parts.
        parts = [str(part.get("text", "")) for part in content if isinstance(part, dict) and part.get("type") == "text"]
        return "".join(parts).strip()
    return ""
