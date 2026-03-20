from __future__ import annotations

import hashlib
import json
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
    env["SYNAPSE_OS_ENVIRONMENT"] = "test"
    env["SYNAPSE_OS_RUNTIME_STATE_DIR"] = str(tmp_path / "runtime")
    env["SYNAPSE_OS_RUNS_DB_PATH"] = str(tmp_path / "runs" / "runs.sqlite3")
    env["SYNAPSE_OS_ARTIFACTS_DIR"] = str(tmp_path / "artifacts")
    env["SYNAPSE_OS_WORKSPACE_ROOT"] = str(tmp_path)
    env["SYNAPSE_OS_RUNTIME_POLL_INTERVAL_SECONDS"] = "0.05"
    return env


def _write_auth_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "runtime" / "auth-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "principals": [
                    {"principal_id": "operator-a", "roles": ["operator"]},
                    {"principal_id": "operator-b", "roles": ["operator"]},
                ],
                "tokens": [
                    {
                        "principal_id": "operator-a",
                        "token_sha256": hashlib.sha256(b"operator-a-token").hexdigest(),
                    },
                    {
                        "principal_id": "operator-b",
                        "token_sha256": hashlib.sha256(b"operator-b-token").hexdigest(),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _spawn_runtime_foreground(
    tmp_path: Path,
    *,
    auth_enabled: bool = False,
    auth_token: str | None = None,
) -> subprocess.Popen[str]:
    env = _runtime_env(tmp_path)
    if auth_enabled:
        env["SYNAPSE_OS_AUTH_ENABLED"] = "true"
    if auth_token is not None:
        env["SYNAPSE_OS_AUTH_TOKEN"] = auth_token
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from synapse_os.cli.app import app; app()",
            "runtime",
            "run",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_runtime_ready(tmp_path: Path, process: subprocess.Popen[str]) -> None:
    cli_module = import_module("synapse_os.cli.app")
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
    persistence = import_module("synapse_os.persistence")

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
        "run_context_initialized",
        "run_started",
        "state_transitioned",
        "step_started",
        "step_completed",
        "run_completed",
    ]


def test_run_dispatch_service_auto_queues_when_runtime_process_is_ready(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")
    runtime_service_module = import_module("synapse_os.runtime.service")

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


def test_authenticated_runtime_foreground_worker_skips_incompatible_run_and_processes_next_one(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")

    _write_auth_registry(tmp_path)
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    incompatible_spec = tmp_path / "INCOMPATIBLE.md"
    compatible_spec = tmp_path / "COMPATIBLE.md"
    _write_valid_spec(incompatible_spec)
    _write_valid_spec(compatible_spec)

    incompatible_run_id = repository.create_run(
        spec_path=incompatible_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-b",
    )
    compatible_run_id = repository.create_run(
        spec_path=compatible_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-a",
    )

    process = _spawn_runtime_foreground(
        tmp_path,
        auth_enabled=True,
        auth_token="operator-a-token",
    )
    try:
        _wait_for_runtime_ready(tmp_path, process)
        _wait_for_run_status(repository, compatible_run_id, "completed")
        time.sleep(0.2)
    finally:
        _terminate_process(process)

    compatible_run = repository.get_run(compatible_run_id)
    incompatible_run = repository.get_run(incompatible_run_id)
    incompatible_events = repository.list_events(incompatible_run_id)

    assert compatible_run.status == "completed"
    assert incompatible_run.status == "pending"
    assert incompatible_run.locked is False
    assert [event.event_type for event in incompatible_events] == ["runtime_owner_skip"]
    assert "runtime_started_by=operator-a" in incompatible_events[0].message
    assert "run_initiated_by=operator-b" in incompatible_events[0].message


def test_authenticated_runtime_foreground_worker_processes_legacy_run(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")

    _write_auth_registry(tmp_path)
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    spec_path = tmp_path / "LEGACY.md"
    _write_valid_spec(spec_path)
    legacy_run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="local_cli",
    )

    process = _spawn_runtime_foreground(
        tmp_path,
        auth_enabled=True,
        auth_token="operator-a-token",
    )
    try:
        _wait_for_runtime_ready(tmp_path, process)
        _wait_for_run_status(repository, legacy_run_id, "completed")
    finally:
        _terminate_process(process)

    assert repository.get_run(legacy_run_id).status == "completed"
    assert "runtime_owner_skip" not in [
        event.event_type for event in repository.list_events(legacy_run_id)
    ]


def test_authenticated_runtime_foreground_worker_deduplicates_owner_skip_on_repeated_polls(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")

    _write_auth_registry(tmp_path)
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    spec_path = tmp_path / "ONLY-INCOMPATIBLE.md"
    _write_valid_spec(spec_path)
    incompatible_run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-b",
    )

    process = _spawn_runtime_foreground(
        tmp_path,
        auth_enabled=True,
        auth_token="operator-a-token",
    )
    try:
        _wait_for_runtime_ready(tmp_path, process)
        time.sleep(0.3)
    finally:
        _terminate_process(process)

    incompatible_events = repository.list_events(incompatible_run_id)
    assert [event.event_type for event in incompatible_events] == ["runtime_owner_skip"]


def test_runs_show_surfaces_runtime_owner_skip_for_pending_run(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("synapse_os.persistence")

    env = {
        "SYNAPSE_OS_ENVIRONMENT": "test",
        "SYNAPSE_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "SYNAPSE_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "SYNAPSE_OS_WORKSPACE_ROOT": str(tmp_path),
    }
    _write_auth_registry(tmp_path)
    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    incompatible_spec = tmp_path / "INCOMPATIBLE.md"
    compatible_spec = tmp_path / "COMPATIBLE.md"
    _write_valid_spec(incompatible_spec)
    _write_valid_spec(compatible_spec)
    incompatible_run_id = repository.create_run(
        spec_path=incompatible_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-b",
    )
    repository.create_run(
        spec_path=compatible_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-a",
    )

    process = _spawn_runtime_foreground(
        tmp_path,
        auth_enabled=True,
        auth_token="operator-a-token",
    )
    try:
        _wait_for_runtime_ready(tmp_path, process)
        time.sleep(0.3)
    finally:
        _terminate_process(process)

    result = cli_runner.invoke(cli_app, ["runs", "show", incompatible_run_id], env=env)

    assert result.exit_code == 0
    assert "latest signal" in result.stdout.lower()
    assert "runtime_owner_skip @ REQUEST" in result.stdout
    assert "runtime_started_by=operator-a" in result.stdout
    assert "run_initiated_by=operator-b" in result.stdout
