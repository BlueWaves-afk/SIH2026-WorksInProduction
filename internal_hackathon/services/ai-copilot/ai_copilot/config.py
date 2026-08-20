"""Provider selection; no key is read from source code."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class CopilotSettings(BaseSettings):
    provider: str = "template"
    anthropic_api_key: str | None = None
    sarvam_api_key: str | None = None
    sarvam_base_url: str = "https://api.sarvam.ai/v1"
    model: str = "sarvam-105b-conversations"
    external_provider_allowed: bool = False
    timeout_seconds: float = 20.0
    embedding_model: str | None = None
    max_tokens: int = 700
    model_config = SettingsConfigDict(env_file=(".env.local", ".env"), extra="ignore")
