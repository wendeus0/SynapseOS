from __future__ import annotations

import hashlib
import json
from importlib import import_module
from pathlib import Path


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F29-integration
type: feature
summary: Fixture spec for auth integration tests.
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


def _auth_env(tmp_path: Path) -> dict[str, str]:
    env = {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
        "AIGNT_OS_AUTH_ENABLED": "true",
    }
    return env


def _write_auth_registry(tmp_path: Path) -> Path:
    registry_path = tmp_path / "runtime" / "auth-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "principals": [
                    {"principal_id": "viewer-user", "roles": ["viewer"]},
                    {"principal_id": "operator-user", "roles": ["operator"]},
                ],
                "tokens": [
                    {
                        "principal_id": "viewer-user",
                        "token_sha256": hashlib.sha256(b"viewer-token").hexdigest(),
                    },
                    {
                        "principal_id": "operator-user",
                        "token_sha256": hashlib.sha256(b"operator-token").hexdigest(),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return registry_path


def _write_operator_registry(tmp_path: Path) -> None:
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


def test_runs_submit_preserves_baseline_when_auth_is_disabled(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_ENABLED"] = "false"

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=env,
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    run_record = repository.list_runs()[0]

    assert result.exit_code == 0
    assert run_record.initiated_by == "local_cli"


def test_runs_submit_requires_authentication_when_auth_is_enabled(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_auth_registry(tmp_path)

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=_auth_env(tmp_path),
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 7
    assert (
        "authentication error:" in result.stdout.lower()
        or "authentication error:" in result.stderr.lower()
    )
    assert repository.list_runs() == []


def test_runs_submit_fails_closed_when_auth_registry_is_missing(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)

    result = cli_runner.invoke(
        cli_app,
        [
            "runs",
            "submit",
            str(spec_path),
            "--mode",
            "sync",
            "--stop-at",
            "SPEC_VALIDATION",
            "--auth-token",
            "operator-token",
        ],
        env=_auth_env(tmp_path),
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert repository.list_runs() == []


def test_runs_submit_rejects_viewer_role_for_mutation(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_auth_registry(tmp_path)

    result = cli_runner.invoke(
        cli_app,
        [
            "runs",
            "submit",
            str(spec_path),
            "--mode",
            "sync",
            "--stop-at",
            "SPEC_VALIDATION",
            "--auth-token",
            "viewer-token",
        ],
        env=_auth_env(tmp_path),
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 8
    assert (
        "authorization error:" in result.stdout.lower()
        or "authorization error:" in result.stderr.lower()
    )
    assert repository.list_runs() == []


def test_runs_submit_accepts_operator_and_persists_authenticated_principal(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = "operator-token"

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=env,
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    run_record = repository.list_runs()[0]

    assert result.exit_code == 0
    assert run_record.initiated_by == "operator-user"


def test_runs_submit_async_requires_running_runtime_when_auth_is_enabled(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = "operator-token"

    result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "async", "--stop-at", "SPEC_VALIDATION"],
        env=env,
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert repository.list_runs() == []


def test_runs_submit_async_rejects_runtime_started_by_another_operator(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_operator_registry(tmp_path)
    env = _auth_env(tmp_path)

    start_result = cli_runner.invoke(
        cli_app,
        ["runtime", "start", "--auth-token", "operator-a-token"],
        env=env,
    )
    submit_result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "async", "--auth-token", "operator-b-token"],
        env=env,
    )
    cleanup_result = cli_runner.invoke(
        cli_app,
        ["runtime", "stop", "--auth-token", "operator-a-token"],
        env=env,
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert start_result.exit_code == 0
    assert submit_result.exit_code == 8
    assert (
        "authorization error:" in submit_result.stdout.lower()
        or "authorization error:" in submit_result.stderr.lower()
    )
    assert repository.list_runs() == []
    assert cleanup_result.exit_code == 0


def test_runs_submit_auto_rejects_runtime_started_by_another_operator(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_operator_registry(tmp_path)
    env = _auth_env(tmp_path)

    start_result = cli_runner.invoke(
        cli_app,
        ["runtime", "start", "--auth-token", "operator-a-token"],
        env=env,
    )
    submit_result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "auto", "--auth-token", "operator-b-token"],
        env=env,
    )
    cleanup_result = cli_runner.invoke(
        cli_app,
        ["runtime", "stop", "--auth-token", "operator-a-token"],
        env=env,
    )

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")

    assert start_result.exit_code == 0
    assert submit_result.exit_code == 8
    assert (
        "authorization error:" in submit_result.stdout.lower()
        or "authorization error:" in submit_result.stderr.lower()
    )
    assert repository.list_runs() == []
    assert cleanup_result.exit_code == 0


def test_runs_submit_async_allows_legacy_runtime_binding_without_started_by(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = "operator-token"

    start_result = cli_runner.invoke(cli_app, ["runtime", "start"], env=env)
    runtime_state_path = tmp_path / "runtime" / "runtime-state.json"
    legacy_payload = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    legacy_payload.pop("started_by", None)
    runtime_state_path.write_text(json.dumps(legacy_payload), encoding="utf-8")

    submit_result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "async", "--stop-at", "SPEC_VALIDATION"],
        env=env,
    )
    cleanup_result = cli_runner.invoke(cli_app, ["runtime", "stop"], env=env)

    repository = persistence.RunRepository(tmp_path / "runs" / "runs.sqlite3")
    run_record = repository.list_runs()[0]

    assert start_result.exit_code == 0
    assert submit_result.exit_code == 0
    assert "queued" in submit_result.stdout.lower()
    assert "async" in submit_result.stdout.lower()
    assert run_record.status == "pending"
    assert run_record.initiated_by == "operator-user"
    assert cleanup_result.exit_code == 0


def test_runtime_start_requires_authentication_when_enabled(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)

    result = cli_runner.invoke(cli_app, ["runtime", "start"], env=_auth_env(tmp_path))

    assert result.exit_code == 7
    assert (
        "authentication error:" in result.stdout.lower()
        or "authentication error:" in result.stderr.lower()
    )


def test_runtime_start_rejects_viewer_role(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)

    result = cli_runner.invoke(
        cli_app,
        ["runtime", "start", "--auth-token", "viewer-token"],
        env=_auth_env(tmp_path),
    )

    assert result.exit_code == 8
    assert (
        "authorization error:" in result.stdout.lower()
        or "authorization error:" in result.stderr.lower()
    )


def test_runtime_start_and_stop_accept_operator_token(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = "operator-token"

    start_result = cli_runner.invoke(cli_app, ["runtime", "start"], env=env)
    stop_result = cli_runner.invoke(cli_app, ["runtime", "stop"], env=env)

    assert start_result.exit_code == 0
    assert "running" in start_result.stdout.lower()
    assert stop_result.exit_code == 0
    assert "stopped" in stop_result.stdout.lower()


def test_runtime_status_shows_started_by_for_authenticated_runtime(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = "operator-token"

    start_result = cli_runner.invoke(cli_app, ["runtime", "start"], env=env)
    status_result = cli_runner.invoke(cli_app, ["runtime", "status"], env=env)
    stop_result = cli_runner.invoke(cli_app, ["runtime", "stop"], env=env)

    assert start_result.exit_code == 0
    assert status_result.exit_code == 0
    assert "started by" in status_result.stdout.lower()
    assert "operator-user" in status_result.stdout
    assert stop_result.exit_code == 0


def test_runtime_stop_rejects_different_operator_when_binding_exists(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
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
    env = _auth_env(tmp_path)

    start_result = cli_runner.invoke(
        cli_app,
        ["runtime", "start", "--auth-token", "operator-a-token"],
        env=env,
    )
    stop_result = cli_runner.invoke(
        cli_app,
        ["runtime", "stop", "--auth-token", "operator-b-token"],
        env=env,
    )
    cleanup_result = cli_runner.invoke(
        cli_app,
        ["runtime", "stop", "--auth-token", "operator-a-token"],
        env=env,
    )

    assert start_result.exit_code == 0
    assert stop_result.exit_code == 8
    assert (
        "authorization error:" in stop_result.stdout.lower()
        or "authorization error:" in stop_result.stderr.lower()
    )
    assert cleanup_result.exit_code == 0


def test_runtime_status_marks_legacy_binding_unavailable_under_auth(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = "operator-token"

    start_result = cli_runner.invoke(cli_app, ["runtime", "start"], env=env)
    runtime_state_path = tmp_path / "runtime" / "runtime-state.json"
    legacy_payload = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    legacy_payload.pop("started_by", None)
    runtime_state_path.write_text(
        json.dumps(legacy_payload),
        encoding="utf-8",
    )

    status_result = cli_runner.invoke(cli_app, ["runtime", "status"], env=env)
    stop_result = cli_runner.invoke(cli_app, ["runtime", "stop"], env=env)

    assert start_result.exit_code == 0
    assert status_result.exit_code == 0
    assert "started by" in status_result.stdout.lower()
    assert "unavailable" in status_result.stdout.lower()
    assert stop_result.exit_code == 0


def test_runtime_run_requires_authentication_without_reaching_foreground_exec(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)

    result = cli_runner.invoke(
        cli_app,
        ["runtime", "run", "--process-identity", "fixture-process"],
        env=_auth_env(tmp_path),
    )

    assert result.exit_code == 7
    assert (
        "authentication error:" in result.stdout.lower()
        or "authentication error:" in result.stderr.lower()
    )


def test_runtime_ready_remains_public_even_when_auth_is_enabled(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    _write_auth_registry(tmp_path)

    result = cli_runner.invoke(cli_app, ["runtime", "ready"], env=_auth_env(tmp_path))

    assert result.exit_code == 5
    assert "authentication error:" not in result.stdout.lower()
    assert "authorization error:" not in result.stdout.lower()
