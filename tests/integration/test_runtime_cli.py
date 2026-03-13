from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from importlib import import_module
from pathlib import Path

from typer.testing import CliRunner

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]


def invoke_runtime_command(tmp_path: Path, *args: str):
    cli_module = import_module("aignt_os.cli.app")
    env = {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
    }
    return runner.invoke(cli_module.app, ["runtime", *args], env=env)


def spawn_runtime_foreground(tmp_path: Path) -> subprocess.Popen[str]:
    env = os.environ.copy()
    python_path = str(REPO_ROOT / "src")
    existing_python_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{python_path}{os.pathsep}{existing_python_path}" if existing_python_path else python_path
    )
    env["AIGNT_OS_ENVIRONMENT"] = "test"
    env["AIGNT_OS_RUNTIME_STATE_DIR"] = str(tmp_path)
    env["AIGNT_OS_RUNS_DB_PATH"] = str(tmp_path / "runs" / "runs.sqlite3")
    env["AIGNT_OS_ARTIFACTS_DIR"] = str(tmp_path / "artifacts")
    env["AIGNT_OS_WORKSPACE_ROOT"] = str(tmp_path)

    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from aignt_os.cli.app import app; app()",
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


def terminate_process(process: subprocess.Popen[str]) -> subprocess.CompletedProcess[str]:
    process.terminate()
    try:
        stdout, stderr = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=5)

    return subprocess.CompletedProcess(
        args=process.args,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def wait_for_foreground_runtime_ready(
    tmp_path: Path, process: subprocess.Popen[str], timeout_seconds: float = 5.0
) -> None:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            raise AssertionError(
                "foreground runtime exited before becoming ready\n"
                f"stdout: {stdout}\n"
                f"stderr: {stderr}"
            )

        ready_result = invoke_runtime_command(tmp_path, "ready")
        if ready_result.exit_code == 0:
            return

        time.sleep(0.05)

    raise AssertionError("foreground runtime did not become ready before timeout")


def test_runtime_start_initializes_single_resident_process_and_persists_state(
    tmp_path: Path,
) -> None:
    result = invoke_runtime_command(tmp_path, "start")

    assert result.exit_code == 0
    assert "running" in result.stdout.lower()

    state_files = list(tmp_path.glob("*.json"))
    assert state_files

    persisted_state = json.loads(state_files[0].read_text(encoding="utf-8"))
    assert persisted_state["status"] == "running"
    assert isinstance(persisted_state["pid"], int)
    assert persisted_state["pid"] > 0


def test_runtime_status_reports_running_for_active_runtime(tmp_path: Path) -> None:
    start_result = invoke_runtime_command(tmp_path, "start")
    assert start_result.exit_code == 0

    status_result = invoke_runtime_command(tmp_path, "status")

    assert status_result.exit_code == 0
    assert "aignt os runtime" in status_result.stdout.lower()
    assert "status" in status_result.stdout.lower()
    assert "running" in status_result.stdout.lower()
    assert "pid" in status_result.stdout.lower()


def test_runtime_start_rejects_second_active_process(tmp_path: Path) -> None:
    first_start = invoke_runtime_command(tmp_path, "start")
    assert first_start.exit_code == 0

    second_start = invoke_runtime_command(tmp_path, "start")

    assert second_start.exit_code == 5
    assert (
        "environment error:" in second_start.stdout.lower()
        or "environment error:" in second_start.stderr.lower()
    )
    assert "already" in second_start.stdout.lower() or "already" in second_start.stderr.lower()


def test_runtime_stop_terminates_active_runtime_and_updates_status(tmp_path: Path) -> None:
    start_result = invoke_runtime_command(tmp_path, "start")
    assert start_result.exit_code == 0

    stop_result = invoke_runtime_command(tmp_path, "stop")

    assert stop_result.exit_code == 0
    assert "stopped" in stop_result.stdout.lower()

    status_result = invoke_runtime_command(tmp_path, "status")
    assert status_result.exit_code == 0
    assert "stopped" in status_result.stdout.lower()


def test_runtime_stop_reports_predictable_error_when_runtime_is_not_running(
    tmp_path: Path,
) -> None:
    result = invoke_runtime_command(tmp_path, "stop")

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert "not running" in result.stdout.lower() or "not running" in result.stderr.lower()


def test_runtime_status_reports_inconsistent_for_invalid_persisted_pid(
    tmp_path: Path,
) -> None:
    state_file = tmp_path / "runtime-state.json"
    state_file.write_text(
        json.dumps({"status": "running", "pid": 999_999_999}),
        encoding="utf-8",
    )

    result = invoke_runtime_command(tmp_path, "status")

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert "inconsistent" in result.stdout.lower() or "inconsistent" in result.stderr.lower()


def test_runtime_stop_refuses_to_signal_process_when_persisted_identity_mismatches(
    tmp_path: Path,
) -> None:
    arbitrary_process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        state_file = tmp_path / "runtime-state.json"
        state_file.write_text(
            json.dumps(
                {
                    "status": "running",
                    "pid": arbitrary_process.pid,
                    "started_at": "2026-03-09T00:00:00+00:00",
                    "process_identity": "unexpected-process",
                }
            ),
            encoding="utf-8",
        )

        result = invoke_runtime_command(tmp_path, "stop")

        assert result.exit_code == 5
        assert (
            "environment error:" in result.stdout.lower()
            or "environment error:" in result.stderr.lower()
        )
        assert "inconsistent" in result.stdout.lower() or "inconsistent" in result.stderr.lower()
        assert arbitrary_process.poll() is None
    finally:
        arbitrary_process.terminate()
        arbitrary_process.wait(timeout=5)


def test_runtime_start_rejects_untrusted_state_directory(tmp_path: Path) -> None:
    cli_module = import_module("aignt_os.cli.app")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    env = {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_WORKSPACE_ROOT": str(workspace_root),
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "outside-runtime-state"),
    }

    result = runner.invoke(cli_module.app, ["runtime", "start"], env=env)

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert "state" in result.stdout.lower() or "state" in result.stderr.lower()


def test_runtime_start_rejects_symlinked_state_directory_outside_workspace_root(
    tmp_path: Path,
) -> None:
    cli_module = import_module("aignt_os.cli.app")
    workspace_root = tmp_path / "workspace"
    outside_root = tmp_path / "outside-runtime-state"
    runtime_link = workspace_root / "runtime-link"
    workspace_root.mkdir()
    outside_root.mkdir()
    runtime_link.symlink_to(outside_root, target_is_directory=True)
    env = {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_WORKSPACE_ROOT": str(workspace_root),
        "AIGNT_OS_RUNTIME_STATE_DIR": str(runtime_link),
    }

    result = runner.invoke(cli_module.app, ["runtime", "start"], env=env)

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert "trusted root" in result.stdout.lower() or "trusted root" in result.stderr.lower()


def test_runtime_cli_exposes_foreground_command_for_container_entrypoint(
    tmp_path: Path,
) -> None:
    result = invoke_runtime_command(tmp_path, "run", "--help")

    assert result.exit_code == 0
    assert "run" in result.stdout.lower()


def test_runtime_foreground_command_stays_alive_until_signaled(tmp_path: Path) -> None:
    process = spawn_runtime_foreground(tmp_path)
    try:
        wait_for_foreground_runtime_ready(tmp_path, process)

        assert process.poll() is None

        status_result = invoke_runtime_command(tmp_path, "status")
        assert status_result.exit_code == 0
        assert "running" in status_result.stdout.lower()
    finally:
        completed = terminate_process(process)

    assert completed.returncode == 0


def test_runtime_cli_exposes_readiness_command(tmp_path: Path) -> None:
    result = invoke_runtime_command(tmp_path, "ready")

    assert result.exit_code != 2


def test_runtime_ready_reports_ready_for_running_foreground_runtime(
    tmp_path: Path,
) -> None:
    process = spawn_runtime_foreground(tmp_path)
    try:
        wait_for_foreground_runtime_ready(tmp_path, process)

        ready_result = invoke_runtime_command(tmp_path, "ready")

        assert ready_result.exit_code == 0
        assert "ready" in ready_result.stdout.lower() or "running" in ready_result.stdout.lower()
    finally:
        terminate_process(process)


def test_runtime_ready_fails_when_foreground_identity_token_is_adulterated(
    tmp_path: Path,
) -> None:
    process = spawn_runtime_foreground(tmp_path)
    try:
        wait_for_foreground_runtime_ready(tmp_path, process)

        state_file = tmp_path / "runtime-state.json"
        persisted_state = json.loads(state_file.read_text(encoding="utf-8"))
        persisted_state["process_identity"] = "unexpected-foreground-token"
        state_file.write_text(json.dumps(persisted_state), encoding="utf-8")

        ready_result = invoke_runtime_command(tmp_path, "ready")
        status_result = invoke_runtime_command(tmp_path, "status")

        assert ready_result.exit_code == 5
        assert (
            "environment error:" in ready_result.stdout.lower()
            or "environment error:" in ready_result.stderr.lower()
        )
        assert (
            "not ready" in ready_result.stdout.lower() or "not ready" in ready_result.stderr.lower()
        )
        assert status_result.exit_code == 5
        assert (
            "environment error:" in status_result.stdout.lower()
            or "environment error:" in status_result.stderr.lower()
        )
        assert (
            "inconsistent" in status_result.stdout.lower()
            or "inconsistent" in status_result.stderr.lower()
        )
    finally:
        terminate_process(process)


def test_runtime_ready_fails_when_runtime_is_not_running(tmp_path: Path) -> None:
    result = invoke_runtime_command(tmp_path, "ready")

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert "not ready" in result.stdout.lower() or "not ready" in result.stderr.lower()
