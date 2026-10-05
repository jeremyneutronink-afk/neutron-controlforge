from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "Neutron ControlForge"
    app_version: str = "0.1.0"

    environment: str = "development"
    debug: bool = True

    database_url: str

    # Administrative control-plane credential.
    agentguard_admin_key: str

    # System-security tests deliberately call ControlForge through
    # its real HTTP boundary instead of invoking internal policy
    # functions directly.
    system_test_base_url: str = (
        "http://127.0.0.1:8000"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()