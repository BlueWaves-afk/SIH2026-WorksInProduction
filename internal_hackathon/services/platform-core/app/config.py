"""Environment-layered settings (module_1 spec §4)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/platform"

    # per-source adapter mode: mock | real  (M3)
    adapter_mode_imd: str = "mock"
    adapter_mode_agmarknet: str = "mock"
    adapter_mode_agristack: str = "mock"
    adapter_mode_bhashini: str = "mock"
    adapter_mode_bhuvan: str = "mock"

    notify_provider: str = "mock"          # M6
    shadow_ml_enabled: bool = False        # M7


settings = Settings()
