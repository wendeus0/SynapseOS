from __future__ import annotations

import os
import subprocess
import sys
import time
from importlib import import_module
from pathlib import Path

from typer.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F08-integration
type: feature
summary: Fixture spec for worker runtime integration tests.
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


def _runtime_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    python_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{python_path}{os.pathsep}{existing}" if existing else python_path
    env["AIGNT_OS_ENVIRONMENT"] = "test"
    env["AIGNT_OS_RUNTIME_STATE_DIR"] = str(tmp_path / "runtime")
    env["AIGNT_OS_RUNS_DB_PATH"] = str(tmp_path / "runs" / "runs.sqlite3")
    env["AIGNT_OS_ARTIFACTS_DIR"] = str(tmp_path / "artifacts")
    env["AIGNT_OS_RUNTIME_POLL_INTERVAL_SECONDS"] = "0.05"
    return env


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
        env=_runtime_env(tmp_path),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_runtime_ready(tmp_path: Path, process: subprocess.Popen[str]) -> None:
    cli_module = import_module("aignt_os.cli.app")
    runner = CliRunner()
    deadline = time.monotonic() + 5.0
    env = _runtime_env(tmp_path)

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


def _wait_for_run_status(repository, run_id: str, expected_status: str) -> None:  # type: ignore[no-untyped-def]
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if repository.get_run(run_id).status == expected_status:
            return
        time.sleep(0.05)
    raise AssertionError(f"run {run_id} did not reach status {expected_status!r}")


def _terminate_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=5)


def test_runtime_foreground_worker_consumes_pending_run(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
    )

    process = _spawn_runtime_foreground(tmp_path)
    try:
        _wait_for_runtime_ready(tmp_path, process)
        _wait_for_run_status(repository, run_id, "completed")
    finally:
        _terminate_process(process)

    run_record = repository.get_run(run_id)
    events = repository.list_events(run_id)
    steps = repository.list_steps(run_id)
    assert run_record.current_state == "SPEC_VALIDATION"
    assert [step.state for step in steps] == ["SPEC_VALIDATION"]
    assert [event.event_type for event in events] == [
        "run_started",
        "step_completed",
        "run_completed",
    ]


def test_run_dispatch_service_auto_queues_when_runtime_process_is_ready(
    tmp_path: Path,
) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")
    runtime_service_module = import_module("aignt_os.runtime.service")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    runtime_service = runtime_service_module.RuntimeService(
        tmp_path / "runtime" / "runtime-state.json"
    )
    dispatch_service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=runtime_service.ready,
        workspace_root=tmp_path,
    )

    runtime_service.start()
    try:
        result = dispatch_service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="auto")
    finally:
        runtime_service.stop()

    run_record = repository.get_run(result.run_id)
    assert result.status == "queued"
    assert result.dispatch_mode_resolved == "async"
    assert run_record.status == "pending"
