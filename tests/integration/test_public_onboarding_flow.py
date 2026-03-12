from __future__ import annotations

import re
from pathlib import Path


def _onboarding_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
    }


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F20-integration
type: feature
summary: Fixture spec for public onboarding integration tests.
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


def _extract_run_id(stdout: str) -> str:
    match = re.search(r"run_id:\s+([a-f0-9-]+)", stdout, re.IGNORECASE)
    if match is None:
        raise AssertionError(f"run_id not found in CLI output:\n{stdout}")
    return match.group(1)


def test_public_onboarding_sequence_is_executable_via_public_cli(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    env = _onboarding_env(tmp_path)
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)

    doctor_result = cli_runner.invoke(cli_app, ["doctor"], env=env)

    assert doctor_result.exit_code == 0
    assert "runtime_state" in doctor_result.stdout
    assert "runs_db" in doctor_result.stdout
    assert "artifacts_dir" in doctor_result.stdout
    assert "warn" in doctor_result.stdout.lower()

    submit_result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=env,
    )

    assert submit_result.exit_code == 0
    run_id = _extract_run_id(submit_result.stdout)

    show_result = cli_runner.invoke(cli_app, ["runs", "show", run_id], env=env)

    assert show_result.exit_code == 0
    assert run_id in show_result.stdout
    assert "completed" in show_result.stdout.lower()
    assert "spec_validation" in show_result.stdout.lower()
    assert "canonical happy path is complete" in show_result.stdout.lower()
