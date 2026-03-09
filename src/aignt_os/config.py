from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIGNT_OS_",
        extra="ignore",
    )

    app_name: str = "AIgnt OS"
    environment: Literal["development", "test", "production"] = "development"
    runtime_state_dir: Path = Path(".aignt-os/runtime")

    @property
    def runtime_state_file(self) -> Path:
        return self.runtime_state_dir / "runtime-state.json"
