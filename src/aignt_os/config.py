from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aignt_os.security import DEFAULT_SECRET_MASK_PATTERNS


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIGNT_OS_",
        extra="ignore",
    )

    app_name: str = "AIgnt OS"
    environment: Literal["development", "test", "production"] = "development"
    runtime_state_dir: Path = Path(".aignt-os/runtime")
    runs_db_path: Path = Path(".aignt-os/runs/runs.sqlite3")
    artifacts_dir: Path = Path(".aignt-os/artifacts")
    workspace_root: Path = Field(default_factory=Path.cwd)
    runtime_poll_interval_seconds: float = 0.5
    secret_mask_patterns: list[str] = list(DEFAULT_SECRET_MASK_PATTERNS)

    @property
    def runtime_state_file(self) -> Path:
        return self.runtime_state_dir / "runtime-state.json"
