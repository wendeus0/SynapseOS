from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path


def _submit_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
    }


def _runtime_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
    }


def test_runs_submit_invalid_mode_returns_usage_error_code(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text(
        """---
id: F21-fixture
type: feature
summary: Fixture spec for CLI error model tests.
inputs:
  - raw_request
outputs:
  - validated_spec
acceptance_criteria:
  - must validate
non_goals: []
---

# Contexto

Fixture context.

# Objetivo

Fixture objective.
""",
        encoding="utf-8",
    )

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "invalid"],
        env=_submit_env(tmp_path),
    )

    assert result.exit_code == 2
    assert "usage error:" in result.stdout.lower() or "usage error:" in result.stderr.lower()


def test_runtime_ready_returns_environment_error_code(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    result = cli_runner.invoke(cli_app, ["runtime", "ready"], env=_runtime_env(tmp_path))

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )


def test_runtime_status_inconsistent_returns_environment_error_code(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    state_file = tmp_path / "runtime-state.json"
    state_file.write_text(
        json.dumps({"status": "running", "pid": 999_999_999}),
        encoding="utf-8",
    )

    result = cli_runner.invoke(cli_app, ["runtime", "status"], env=_runtime_env(tmp_path))

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )


def test_cli_preserves_typer_parse_error_exit_code(
    cli_runner,
    cli_app,
) -> None:
    result = cli_runner.invoke(cli_app, ["runs", "submit"])

    assert result.exit_code == 2
    assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()


def test_runs_submit_unexpected_dispatch_failure_returns_execution_error_code(
    tmp_path: Path,
    cli_runner,
    monkeypatch,
) -> None:
    cli_module = import_module("aignt_os.cli.app")

    class _BrokenDispatchService:
        def dispatch(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("dispatch exploded")

    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text(
        """---
id: F21-fixture
type: feature
summary: Fixture spec for unexpected dispatch failure.
inputs:
  - raw_request
outputs:
  - validated_spec
acceptance_criteria:
  - must validate
non_goals: []
---

# Contexto

Fixture context.

# Objetivo

Fixture objective.
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli_module, "_dispatch_service", lambda: _BrokenDispatchService())

    result = cli_runner.invoke(
        cli_module.app,
        ["runs", "submit", str(spec_path)],
        env=_submit_env(tmp_path),
    )

    assert result.exit_code == 6
    assert (
        "execution error:" in result.stdout.lower() or "execution error:" in result.stderr.lower()
    )
