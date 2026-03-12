from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import time
from importlib import import_module
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F15-integration
type: feature
summary: Fixture spec for runs submit integration tests.
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


def _submit_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    python_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{python_path}{os.pathsep}{existing}" if existing else python_path
    env["AIGNT_OS_ENVIRONMENT"] = "test"
    env["AIGNT_OS_RUNTIME_STATE_DIR"] = str(tmp_path / "runtime")
    env["AIGNT_OS_RUNS_DB_PATH"] = str(tmp_path / "runs" / "runs.sqlite3")
    env["AIGNT_OS_ARTIFACTS_DIR"] = str(tmp_path / "artifacts")
    env["AIGNT_OS_WORKSPACE_ROOT"] = str(tmp_path)
    env["AIGNT_OS_RUNTIME_POLL_INTERVAL_SECONDS"] = "0.05"
    return env


def _extract_run_id(stdout: str) -> str:
    match = re.search(r"run_id:\s+([a-f0-9-]+)", stdout, re.IGNORECASE)
    if match is None:
        raise AssertionError(f"run_id not found in CLI output:\n{stdout}")
    return match.group(1)


def _spawn_runtime_foreground(tmp_path: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from aignt_os.cli.app import app; app()",
            "runtime",
            "run",
        ],
        cwd=REPO_ROOT,
        env=_submit_env(tmp_path),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_runtime_ready(tmp_path: Path, process: subprocess.Popen[str]) -> None:
    cli_module = import_module("aignt_os.cli.app")
    runner = import_module("typer.testing").CliRunner()
    deadline = time.monotonic() + 5.0
    env = _submit_env(tmp_path)

    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            raise AssertionError(
                "foreground runtime exited before becoming ready\n"
                f"stdout: {stdout}\n"
                f"stderr: {stderr}"
            )

        result = runner.invoke(cli_module.app, ["runtime", "ready"], env=env)
        if result.exit_code == 0:
            return

        time.sleep(0.05)

    raise AssertionError("foreground runtime did not become ready before timeout")


def _terminate_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=5)


def test_runs_submit_sync_executes_inline_and_reports_contract(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=_submit_env(tmp_path),
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    run_record = repository.list_runs()[0]

    assert result.exit_code == 0
    assert "run_id" in result.stdout.lower()
    assert "status" in result.stdout.lower()
    assert "mode" in result.stdout.lower()
    assert run_record.run_id in result.stdout
    assert "completed" in result.stdout.lower()
    assert "sync" in result.stdout.lower()
    assert run_record.status == "completed"
    assert run_record.current_state == "SPEC_VALIDATION"
    assert run_record.initiated_by == "local_cli"
    assert run_record.spec_hash == hashlib.sha256(spec_path.read_bytes()).hexdigest()


def test_canonical_happy_path_submit_then_show_is_auditable_via_public_cli(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    env = _submit_env(tmp_path)

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
    assert "status" in show_result.stdout.lower()
    assert "completed" in show_result.stdout.lower()
    assert "current state" in show_result.stdout.lower()
    assert "spec_validation" in show_result.stdout.lower()
    assert "latest signal" in show_result.stdout.lower()
    assert "spec path" in show_result.stdout.lower()
    assert "spec hash" in show_result.stdout.lower()
    assert "initiated by" in show_result.stdout.lower()
    assert str(spec_path) in show_result.stdout
    assert hashlib.sha256(spec_path.read_bytes()).hexdigest() in show_result.stdout
    assert "local_cli" in show_result.stdout
    assert "next action" in show_result.stdout.lower()
    assert "canonical happy path is complete" in show_result.stdout.lower()


def test_runs_submit_auto_queues_when_runtime_is_ready(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")
    runtime_service_module = import_module("aignt_os.runtime.service")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)

    runtime_service = runtime_service_module.RuntimeService(
        tmp_path / "runtime" / "runtime-state.json"
    )
    try:
        runtime_service.start()
        result = cli_runner.invoke(
            cli_app,
            ["runs", "submit", str(spec_path), "--mode", "auto", "--stop-at", "SPEC_VALIDATION"],
            env=_submit_env(tmp_path),
        )
    finally:
        runtime_service.stop()

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    run_record = repository.list_runs()[0]

    assert result.exit_code == 0
    assert run_record.run_id in result.stdout
    assert "queued" in result.stdout.lower()
    assert "async" in result.stdout.lower()
    assert run_record.status == "pending"
    assert run_record.current_state == "REQUEST"
    assert run_record.initiated_by == "local_cli"
    assert run_record.spec_hash == hashlib.sha256(spec_path.read_bytes()).hexdigest()


def test_runs_submit_fails_predictably_when_spec_is_missing(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    missing_spec_path = tmp_path / "missing.md"

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(missing_spec_path)],
        env=_submit_env(tmp_path),
    )

    persistence = import_module("aignt_os.persistence")
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 3
    assert "not found:" in result.stdout.lower() or "not found:" in result.stderr.lower()
    assert repository.list_runs() == []


def test_runs_submit_fails_predictably_when_spec_is_invalid(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    invalid_spec_path = tmp_path / "SPEC.md"
    invalid_spec_path.write_text("# Contexto\n\nSem front matter.\n", encoding="utf-8")

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(invalid_spec_path)],
        env=_submit_env(tmp_path),
    )

    persistence = import_module("aignt_os.persistence")
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 4
    assert (
        "validation error:" in result.stdout.lower() or "validation error:" in result.stderr.lower()
    )
    assert repository.list_runs() == []


def test_runs_submit_rejects_spec_outside_workspace_root(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside_spec_path = tmp_path / "outside" / "SPEC.md"
    outside_spec_path.parent.mkdir()
    _write_valid_spec(outside_spec_path)

    env = _submit_env(tmp_path)
    env["AIGNT_OS_WORKSPACE_ROOT"] = str(workspace_root)

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(outside_spec_path)],
        env=env,
    )

    persistence = import_module("aignt_os.persistence")
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 3
    assert "not found:" in result.stdout.lower() or "not found:" in result.stderr.lower()
    assert repository.list_runs() == []


def test_runs_submit_rejects_symlinked_spec_that_resolves_outside_workspace_root(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside_spec_path = tmp_path / "outside" / "SPEC.md"
    outside_spec_path.parent.mkdir()
    _write_valid_spec(outside_spec_path)
    escaped_spec_path = workspace_root / "SPEC.md"
    escaped_spec_path.symlink_to(outside_spec_path)

    env = _submit_env(tmp_path)
    env["AIGNT_OS_WORKSPACE_ROOT"] = str(workspace_root)

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(escaped_spec_path)],
        env=env,
    )

    persistence = import_module("aignt_os.persistence")
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 3
    assert "not found:" in result.stdout.lower() or "not found:" in result.stderr.lower()
    assert repository.list_runs() == []
