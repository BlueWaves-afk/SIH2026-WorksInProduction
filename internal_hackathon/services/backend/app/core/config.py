"""Single source of truth for backend configuration.

Secrets are deliberately read from ``.env.local`` (or the hosting provider's
environment) and are never checked into the repository.  ``.env.example`` is
documentation only.  Supabase is the production identity and Postgres
provider; SQLite is available only as a local, dependency-free fallback.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "KisanSetu Backend"
    api_v1_str: str = "/api/v1"
    env: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./kisansetu.local.db"

    # Supabase Auth / Postgres.  Values are intentionally optional for local
    # fixture mode and required by deployment validation when AUTH_REQUIRED is
    # enabled.
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_key: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_audience: str = "authenticated"
    vault_encryption_key: str | None = None
    auth_required: bool = False

    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    request_timeout_seconds: float = 10.0
    quiet_hours_start: int = Field(default=21, ge=0, le=23)
    quiet_hours_end: int = Field(default=7, ge=0, le=23)
    outreach_daily_cap: int = Field(default=2, ge=1, le=20)
    observation_retention_days: int = Field(default=90, ge=7, le=3650)
    outbox_retention_days: int = Field(default=30, ge=7, le=3650)
    notify_provider: str = "mock"
    notification_webhook_secret: str | None = None
    sms_provider_key: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_graph_api_version: str = "v20.0"
    whatsapp_base_url: str = "https://graph.facebook.com"
    whatsapp_template_name: str | None = None
    whatsapp_call_endpoint: str | None = None
    whatsapp_call_api_key: str | None = None
    whatsapp_call_provider: str = "partner"
    sarvam_voice_agent_base_url: str = "https://apps.sarvam.ai"
    sarvam_voice_agent_api_key: str | None = None
    sarvam_voice_agent_org_id: str | None = None
    sarvam_voice_agent_workspace_id: str | None = None
    sarvam_voice_agent_app_id: str | None = None
    sarvam_voice_agent_app_version: int = Field(default=1, ge=1)
    sarvam_voice_agent_connection_id: str | None = None
    sarvam_voice_agent_phone_number: str | None = None
    bhashini_api_key: str | None = None
    # LLM calls are server-side only.  The safe default keeps local/demo
    # deployments deterministic; enabling a provider is an explicit release
    # decision via LLM_EXTERNAL_ALLOWED=true.
    llm_provider: str = "template"
    llm_model: str = "sarvam-105b-conversations"
    llm_external_allowed: bool = False
    llm_max_output_tokens: int = Field(default=256, ge=32, le=2048)
    sarvam_api_key: str | None = None
    sarvam_base_url: str = "https://api.sarvam.ai/v1"
    sarvam_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    sarvam_stt_endpoint: str = "https://api.sarvam.ai/speech-to-text"
    sarvam_tts_endpoint: str = "https://api.sarvam.ai/text-to-speech"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_tts_voice: str = "shubh"
    imd_api_key: str | None = None
    agmarknet_api_key: str | None = None
    # Live ingestion is opt-in.  The application stays on deterministic
    # fixtures until both the feature flag and the source adapter mode are
    # enabled, preventing an incomplete deployment from fabricating freshness.
    live_data_enabled: bool = False
    live_adapter_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    imd_endpoint: str | None = None
    agmarknet_endpoint: str | None = None
    agristack_endpoint: str | None = None
    bhashini_endpoint: str | None = None
    bhuvan_endpoint: str | None = None
    msp_endpoint: str | None = None
    sentinel2_endpoint: str | None = None
    soil_endpoint: str | None = None
    adapter_mode_imd: str = "mock"
    adapter_mode_agmarknet: str = "mock"
    adapter_mode_agristack: str = "mock"
    adapter_mode_bhashini: str = "mock"
    adapter_mode_bhuvan: str = "mock"
    adapter_mode_msp: str = "mock"
    adapter_mode_sentinel2: str = "mock"
    adapter_mode_soil: str = "mock"
    agristack_api_key: str | None = None
    bhuvan_api_key: str | None = None
    msp_api_key: str | None = None
    sentinel2_api_key: str | None = None
    sentinel2_client_id: str | None = None
    sentinel2_client_secret: str | None = None
    sentinel2_token_url: str | None = None
    soil_api_key: str | None = None
    live_signal_sources: str = "imd,agmarknet"
    shadow_ml_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def live_signal_source_list(self) -> list[str]:
        # AgriStack profile prefill and Bhashini voice are separate contracts;
        # they are health-checked but are not signal rows for the FDI scorer.
        allowed = {"imd", "agmarknet", "bhuvan", "msp", "sentinel2", "soil"}
        selected = [item.strip().lower() for item in self.live_signal_sources.split(",") if item.strip()]
        if not selected:
            raise RuntimeError("LIVE_SIGNAL_SOURCES must contain at least one signal source")
        invalid = sorted(set(selected) - allowed)
        if invalid:
            raise RuntimeError(f"LIVE_SIGNAL_SOURCES contains unsupported sources: {', '.join(invalid)}")
        return list(dict.fromkeys(selected))

    def validate_production(self) -> None:
        if self.env.lower() in {"production", "staging"}:
            required = {
                "SUPABASE_URL": self.supabase_url,
                "DATABASE_URL": self.database_url,
                "VAULT_ENCRYPTION_KEY": self.vault_encryption_key,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise RuntimeError(f"Missing required production settings: {', '.join(missing)}")
        if self.llm_provider.lower() == "sarvam" and self.llm_external_allowed and not self.sarvam_api_key:
            raise RuntimeError("SARVAM_API_KEY is required when live Sarvam is enabled")
        if self.notify_provider.lower() in {"whatsapp", "meta", "whatsapp_cloud"}:
            missing_whatsapp = {
                "WHATSAPP_ACCESS_TOKEN": self.whatsapp_access_token,
                "WHATSAPP_PHONE_NUMBER_ID": self.whatsapp_phone_number_id,
            }
            missing = [name for name, value in missing_whatsapp.items() if not value]
            if missing:
                raise RuntimeError(f"Missing WhatsApp provider settings: {', '.join(missing)}")
            if self.whatsapp_call_provider.lower() == "sarvam":
                sarvam_call = {
                    "SARVAM_VOICE_AGENT_API_KEY": self.sarvam_voice_agent_api_key or self.sarvam_api_key,
                    "SARVAM_VOICE_AGENT_ORG_ID": self.sarvam_voice_agent_org_id,
                    "SARVAM_VOICE_AGENT_WORKSPACE_ID": self.sarvam_voice_agent_workspace_id,
                    "SARVAM_VOICE_AGENT_APP_ID": self.sarvam_voice_agent_app_id,
                    "SARVAM_VOICE_AGENT_CONNECTION_ID": self.sarvam_voice_agent_connection_id,
                    "SARVAM_VOICE_AGENT_PHONE_NUMBER": self.sarvam_voice_agent_phone_number,
                }
                missing_call = [name for name, value in sarvam_call.items() if not value]
                if missing_call:
                    raise RuntimeError(f"Missing Sarvam Voice Agents settings: {', '.join(missing_call)}")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings


settings = get_settings()
