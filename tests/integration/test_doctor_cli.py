from __future__ import annotations

import json
from pathlib import Path


def _doctor_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
    }


def test_doctor_reports_minimum_healthy_environment_with_runtime_warn(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    result = cli_runner.invoke(cli_app, ["doctor"], env=_doctor_env(tmp_path))

    assert result.exit_code == 0
    assert "environment doctor" in result.stdout.lower()
    assert "overall status" in result.stdout.lower()
    assert "pass" in result.stdout.lower()
    assert "runtime_state" in result.stdout
    assert "runs_db" in result.stdout
    assert "artifacts_dir" in result.stdout
    assert "warn" in result.stdout.lower()
    assert "next step" in result.stdout.lower()
    assert "traceback" not in result.stdout.lower()
    assert "traceback" not in result.stderr.lower()


def test_doctor_returns_environment_error_when_runtime_state_is_inconsistent(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    runtime_state_dir = tmp_path / "runtime"
    runtime_state_dir.mkdir(parents=True)
    (runtime_state_dir / "runtime-state.json").write_text(
        json.dumps({"status": "running", "pid": 999_999_999}),
        encoding="utf-8",
    )

    result = cli_runner.invoke(cli_app, ["doctor"], env=_doctor_env(tmp_path))

    assert result.exit_code == 5
    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    assert "environment doctor" in combined_output
    assert "runtime_state" in combined_output
    assert "fail" in combined_output
    assert "traceback" not in combined_output


def test_doctor_returns_environment_error_when_runs_db_parent_is_not_writable(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    blocked_parent = tmp_path / "blocked-parent"
    blocked_parent.write_text("not a directory", encoding="utf-8")

    env = {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(blocked_parent / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
    }

    result = cli_runner.invoke(cli_app, ["doctor"], env=env)

    assert result.exit_code == 5
    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    assert "runs_db" in combined_output
    assert "fail" in combined_output
    assert "fix" in combined_output or "permission" in combined_output or "path" in combined_output
    assert "traceback" not in combined_output
