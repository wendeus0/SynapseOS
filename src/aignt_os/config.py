from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aignt_os.security import DEFAULT_SECRET_MASK_PATTERNS, resolve_path_within_root


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
    run_initiated_by: str = "local_cli"
    max_concurrent_adapters: int = Field(default=4, gt=0)
    adapter_circuit_breaker_failure_threshold: int = Field(default=2, gt=0)
    adapter_circuit_breaker_cooldown_seconds: float = Field(default=60.0, gt=0)
    auth_enabled: bool = False
    auth_provider: Literal["file"] = "file"
    secret_mask_patterns: list[str] = list(DEFAULT_SECRET_MASK_PATTERNS)

    execution_timeout_seconds: float = Field(default=300.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    tui_log_buffer_lines: int = Field(default=1000, gt=0)

    @property
    def runtime_state_dir_resolved(self) -> Path:
        return resolve_path_within_root(self.runtime_state_dir, root=self.workspace_root)

    @property
    def runs_db_path_resolved(self) -> Path:
        return resolve_path_within_root(self.runs_db_path, root=self.workspace_root)

    @property
    def artifacts_dir_resolved(self) -> Path:
        return resolve_path_within_root(self.artifacts_dir, root=self.workspace_root)

    @property
    def runtime_state_file(self) -> Path:
        return self.runtime_state_dir_resolved / "runtime-state.json"

    @property
    def adapter_circuit_breaker_state_file(self) -> Path:
        return self.runtime_state_dir_resolved / "adapter-circuit-breakers.json"

    @property
    def auth_registry_file(self) -> Path:
        return self.runtime_state_dir_resolved / "auth-registry.json"
