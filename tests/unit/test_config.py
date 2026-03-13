from importlib import import_module
from pathlib import Path

import pytest
from pydantic import ValidationError


def test_settings_exposes_default_values() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.model_dump()["app_name"]
    assert settings.model_dump()["environment"]


def test_settings_exposes_all_expected_default_paths() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert isinstance(settings.runtime_state_dir, Path)
    assert isinstance(settings.runs_db_path, Path)
    assert isinstance(settings.artifacts_dir, Path)
    assert isinstance(settings.workspace_root, Path)
    assert settings.secret_mask_patterns


def test_settings_default_runs_db_path_is_sqlite_under_aignt_dir() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.runs_db_path.suffix == ".sqlite3"
    assert ".aignt-os" in str(settings.runs_db_path)


def test_settings_default_artifacts_dir_is_under_aignt_dir() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert ".aignt-os" in str(settings.artifacts_dir)


def test_settings_accepts_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_APP_NAME", "AIgnt OS Test")

    settings = config_module.AppSettings()

    assert settings.app_name == "AIgnt OS Test"


def test_settings_exposes_runtime_state_file(monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", ".runtime-state")

    settings = config_module.AppSettings()

    assert settings.runtime_state_dir.name == ".runtime-state"
    assert settings.runtime_state_file.name == "runtime-state.json"


def test_settings_exposes_run_persistence_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_RUNS_DB_PATH", ".runtime/runs.sqlite3")
    monkeypatch.setenv("AIGNT_OS_ARTIFACTS_DIR", ".runtime/artifacts")

    settings = config_module.AppSettings()

    assert settings.runs_db_path.name == "runs.sqlite3"
    assert settings.artifacts_dir.name == "artifacts"


def test_settings_runtime_state_file_is_child_of_state_dir() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.runtime_state_file.parent == settings.runtime_state_dir_resolved


def test_settings_workspace_root_defaults_to_current_working_directory() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.workspace_root == Path.cwd()


def test_settings_accepts_workspace_root_override(monkeypatch: pytest.MonkeyPatch) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", ".workspace-root")

    settings = config_module.AppSettings()

    assert settings.workspace_root == Path(".workspace-root")


def test_settings_workspace_root_uses_current_working_directory_at_instantiation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.chdir(tmp_path)

    settings = config_module.AppSettings()

    assert settings.workspace_root == tmp_path


def test_settings_exposes_default_secret_mask_patterns() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert any("ghp_" in pattern for pattern in settings.secret_mask_patterns)
    assert any("ghs_" in pattern for pattern in settings.secret_mask_patterns)
    assert any("sk-" in pattern for pattern in settings.secret_mask_patterns)


def test_settings_exposes_default_run_initiated_by() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.run_initiated_by == "local_cli"


def test_settings_exposes_default_max_concurrent_adapters() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.max_concurrent_adapters == 4


def test_settings_exposes_default_adapter_circuit_breaker_controls() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.adapter_circuit_breaker_failure_threshold == 2
    assert settings.adapter_circuit_breaker_cooldown_seconds == 60.0
    assert settings.adapter_circuit_breaker_state_file.name == "adapter-circuit-breakers.json"
    assert settings.adapter_circuit_breaker_state_file.parent == settings.runtime_state_dir_resolved


def test_settings_exposes_default_auth_controls() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert settings.auth_enabled is False
    assert settings.auth_registry_file.name == "auth-registry.json"
    assert settings.auth_registry_file.parent == settings.runtime_state_dir_resolved


def test_settings_resolves_runtime_state_dir_within_workspace_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", str(tmp_path / "runtime"))

    settings = config_module.AppSettings()

    assert settings.runtime_state_dir_resolved == (tmp_path / "runtime").resolve()
    assert settings.runtime_state_file.parent == settings.runtime_state_dir_resolved


def test_settings_rejects_runtime_state_dir_outside_workspace_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_module = import_module("aignt_os.config")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", str(workspace_root))
    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", str(tmp_path / "outside-runtime"))

    settings = config_module.AppSettings()

    with pytest.raises(ValueError, match="Path escapes trusted root"):
        _ = settings.runtime_state_file

    with pytest.raises(ValueError, match="Path escapes trusted root"):
        _ = settings.auth_registry_file


def test_settings_rejects_symlinked_runtime_state_dir_that_resolves_outside_workspace_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_module = import_module("aignt_os.config")
    workspace_root = tmp_path / "workspace"
    outside_root = tmp_path / "outside-runtime"
    runtime_link = workspace_root / "runtime-link"
    workspace_root.mkdir()
    outside_root.mkdir()
    runtime_link.symlink_to(outside_root, target_is_directory=True)
    monkeypatch.setenv("AIGNT_OS_WORKSPACE_ROOT", str(workspace_root))
    monkeypatch.setenv("AIGNT_OS_RUNTIME_STATE_DIR", str(runtime_link))

    settings = config_module.AppSettings()

    with pytest.raises(ValueError, match="Path escapes trusted root"):
        _ = settings.adapter_circuit_breaker_state_file


def test_settings_rejects_invalid_environment_value() -> None:
    config_module = import_module("aignt_os.config")

    with pytest.raises(ValidationError):
        config_module.AppSettings(environment="invalid")


def test_settings_rejects_non_positive_max_concurrent_adapters() -> None:
    config_module = import_module("aignt_os.config")

    with pytest.raises(ValidationError):
        config_module.AppSettings(max_concurrent_adapters=0)


def test_settings_rejects_non_positive_adapter_circuit_breaker_threshold() -> None:
    config_module = import_module("aignt_os.config")

    with pytest.raises(ValidationError):
        config_module.AppSettings(adapter_circuit_breaker_failure_threshold=0)


def test_settings_rejects_non_positive_adapter_circuit_breaker_cooldown() -> None:
    config_module = import_module("aignt_os.config")

    with pytest.raises(ValidationError):
        config_module.AppSettings(adapter_circuit_breaker_cooldown_seconds=0)


@pytest.mark.parametrize(
    "env_value",
    ["development", "test", "production"],
)
def test_settings_accepts_all_valid_environment_values(
    monkeypatch: pytest.MonkeyPatch, env_value: str
) -> None:
    config_module = import_module("aignt_os.config")
    monkeypatch.setenv("AIGNT_OS_ENVIRONMENT", env_value)

    settings = config_module.AppSettings()

    assert settings.environment == env_value
