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

    assert settings.runtime_state_file.parent == settings.runtime_state_dir


def test_settings_exposes_default_secret_mask_patterns() -> None:
    config_module = import_module("aignt_os.config")

    settings = config_module.AppSettings()

    assert any("ghp_" in pattern for pattern in settings.secret_mask_patterns)
    assert any("ghs_" in pattern for pattern in settings.secret_mask_patterns)
    assert any("sk-" in pattern for pattern in settings.secret_mask_patterns)


def test_settings_rejects_invalid_environment_value() -> None:
    config_module = import_module("aignt_os.config")

    with pytest.raises(ValidationError):
        config_module.AppSettings(environment="invalid")


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
