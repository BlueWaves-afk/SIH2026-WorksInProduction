"""Provider selection; no key is read from source code."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class CopilotSettings(BaseSettings):
    provider: str = "template"
    anthropic_api_key: str | None = None
    embedding_model: str | None = None
    max_tokens: int = 700
    model_config = SettingsConfigDict(env_file=(".env.local", ".env"), extra="ignore")
