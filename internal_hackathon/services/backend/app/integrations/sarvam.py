"""Server-side Sarvam chat provider.

The browser never receives the Sarvam subscription key.  This adapter speaks
Sarvam's OpenAI-compatible chat-completions contract and deliberately exposes
only the small surface needed by the bounded farmer-support agent.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from app.core.config import Settings


class SarvamProviderError(RuntimeError):
    """A provider failure that is safe to surface as a deterministic fallback."""


class SarvamSpeechProviderError(RuntimeError):
    """A speech-provider failure safe to surface as an offline fallback."""


@dataclass(frozen=True)
class SarvamChatResult:
    content: str
    model: str
    provider: str = "sarvam"


@dataclass(frozen=True)
class SarvamTranscription:
    text: str
    language: str | None = None
    confidence: float | None = None


class SarvamSpeechProvider:
    """Server-side Sarvam STT/TTS adapter used instead of Bhashini.

    The adapter deliberately exposes bytes/text only.  It does not persist
    audio, log the API key, or make any scoring or outreach decision.
    """

    def __init__(
        self,
        *,
        api_key: str | None,
        stt_endpoint: str = "https://api.sarvam.ai/speech-to-text",
        tts_endpoint: str = "https://api.sarvam.ai/text-to-speech",
        stt_model: str = "saaras:v3",
        tts_model: str = "bulbul:v3",
        voice: str = "shubh",
        timeout_seconds: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.stt_endpoint = stt_endpoint.rstrip("/")
        self.tts_endpoint = tts_endpoint.rstrip("/")
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.voice = voice
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise SarvamSpeechProviderError("Sarvam speech provider is not configured")
        return {"api-subscription-key": self.api_key or "", "accept": "application/json"}

    def transcribe(self, audio: bytes, *, language_code: str | None = None) -> SarvamTranscription:
        if not audio:
            raise SarvamSpeechProviderError("audio payload is empty")
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            data = {"model": self.stt_model, "mode": "transcribe"}
            if language_code:
                data["language_code"] = language_code
            response = client.post(
                self.stt_endpoint,
                headers=self._headers(),
                data=data,
                files={"file": ("farmer-audio.wav", audio, "audio/wav")},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise SarvamSpeechProviderError(f"Sarvam speech request failed with HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise SarvamSpeechProviderError("Sarvam speech request failed") from exc
        finally:
            if close_client:
                client.close()
        if not isinstance(payload, dict):
            raise SarvamSpeechProviderError("Sarvam speech response was invalid")
        text = str(payload.get("transcript") or payload.get("text") or "").strip()
        if not text:
            raise SarvamSpeechProviderError("Sarvam speech response contained no transcript")
        confidence = payload.get("confidence")
        try:
            confidence_value = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence_value = None
        return SarvamTranscription(text=text, language=payload.get("language_code"), confidence=confidence_value)

    def synthesize(self, text: str, *, language_code: str = "en-IN") -> bytes:
        if not text.strip():
            raise SarvamSpeechProviderError("TTS text is empty")
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        try:
            response = client.post(
                self.tts_endpoint,
                headers={**self._headers(), "content-type": "application/json"},
                json={
                    "text": text[:2500],
                    "language_code": language_code,
                    "speaker": self.voice,
                    "model": self.tts_model,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise SarvamSpeechProviderError(f"Sarvam TTS request failed with HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise SarvamSpeechProviderError("Sarvam TTS request failed") from exc
        finally:
            if close_client:
                client.close()
        if not isinstance(payload, dict):
            raise SarvamSpeechProviderError("Sarvam TTS response was invalid")
        audio_b64 = payload.get("audios", [None])[0] if isinstance(payload.get("audios"), list) else None
        if not isinstance(audio_b64, str) or not audio_b64:
            raise SarvamSpeechProviderError("Sarvam TTS response contained no audio")
        try:
            return base64.b64decode(audio_b64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise SarvamSpeechProviderError("Sarvam TTS response contained invalid audio") from exc


def build_sarvam_speech_provider(settings: Settings) -> SarvamSpeechProvider:
    """Build the speech adapter from backend settings without exposing secrets."""

    return SarvamSpeechProvider(
        api_key=settings.sarvam_api_key,
        stt_endpoint=settings.sarvam_stt_endpoint,
        tts_endpoint=settings.sarvam_tts_endpoint,
        stt_model=settings.sarvam_stt_model,
        tts_model=settings.sarvam_tts_model,
        voice=settings.sarvam_tts_voice,
        timeout_seconds=settings.sarvam_timeout_seconds,
    )


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
            # Farmer replies are short and grounded; disabling hidden
            # reasoning prevents a small output budget being consumed before
            # any user-visible content is emitted.
            "reasoning_effort": None,
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
