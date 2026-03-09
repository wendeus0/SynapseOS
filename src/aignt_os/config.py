from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIGNT_OS_",
        extra="ignore",
    )

    app_name: str = "AIgnt OS"
    environment: Literal["development", "test", "production"] = "development"

