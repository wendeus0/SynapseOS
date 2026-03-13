from __future__ import annotations

import hashlib
import json
from pathlib import Path


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
                    {"principal_id": "admin-user", "roles": ["admin"]},
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
                    {
                        "principal_id": "admin-user",
                        "token_sha256": hashlib.sha256(b"admin-token").hexdigest(),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return registry_path


def test_auth_issue_requires_authentication(tmp_path: Path, cli_runner, cli_app):
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)

    result = cli_runner.invoke(
        cli_app, ["auth", "issue", "--principal-id", "new-user", "--role", "viewer"], env=env
    )

    assert result.exit_code == 7  # Auth error
    assert (
        "authentication error" in result.stdout.lower()
        or "authentication error" in result.stderr.lower()
    )


def test_auth_issue_rejects_viewer_and_operator(tmp_path: Path, cli_runner, cli_app):
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)

    # Viewer
    result_viewer = cli_runner.invoke(
        cli_app,
        [
            "auth",
            "issue",
            "--principal-id",
            "new-user",
            "--role",
            "viewer",
            "--auth-token",
            "viewer-token",
        ],
        env=env,
    )
    assert result_viewer.exit_code == 8  # Authorization error

    # Operator
    result_operator = cli_runner.invoke(
        cli_app,
        [
            "auth",
            "issue",
            "--principal-id",
            "new-user",
            "--role",
            "viewer",
            "--auth-token",
            "operator-token",
        ],
        env=env,
    )
    assert result_operator.exit_code == 8


def test_auth_issue_allows_admin(tmp_path: Path, cli_runner, cli_app):
    registry_path = _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)

    result = cli_runner.invoke(
        cli_app,
        [
            "auth",
            "issue",
            "--principal-id",
            "new-user",
            "--role",
            "viewer",
            "--auth-token",
            "admin-token",
        ],
        env=env,
    )

    assert result.exit_code == 0
    assert "Auth Token:" in result.stdout

    # Verify persistence
    content = json.loads(registry_path.read_text())
    assert any(
        p["principal_id"] == "new-user" and "viewer" in p["roles"] for p in content["principals"]
    )


def test_auth_disable_requires_admin(tmp_path: Path, cli_runner, cli_app):
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)

    # Operator fail
    result_fail = cli_runner.invoke(
        cli_app,
        ["auth", "disable", "--token-id", "some-id", "--auth-token", "operator-token"],
        env=env,
    )
    assert result_fail.exit_code == 8

    # Admin success (fail on lookup but pass auth)
    result_success = cli_runner.invoke(
        cli_app,
        ["auth", "disable", "--token-id", "some-id", "--auth-token", "admin-token"],
        env=env,
    )
    # exit code 3 is not_found_error (LookupError)
    assert result_success.exit_code == 3
    assert (
        "not found" in result_success.stdout.lower() or "not found" in result_success.stderr.lower()
    )


def test_runs_list_requires_read_permission(tmp_path: Path, cli_runner, cli_app):
    _write_auth_registry(tmp_path)
    env = _auth_env(tmp_path)

    # Without token
    result_no_token = cli_runner.invoke(cli_app, ["runs", "list"], env=env)
    assert result_no_token.exit_code == 7
    assert (
        "authentication error" in result_no_token.stdout.lower()
        or "authentication error" in result_no_token.stderr.lower()
    )

    # Viewer ok
    result_viewer = cli_runner.invoke(
        cli_app, ["runs", "list", "--auth-token", "viewer-token"], env=env
    )
    assert result_viewer.exit_code == 0

    # Operator ok
    result_operator = cli_runner.invoke(
        cli_app, ["runs", "list", "--auth-token", "operator-token"], env=env
    )
    assert result_operator.exit_code == 0
