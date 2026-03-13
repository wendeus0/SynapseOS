from __future__ import annotations

from importlib import import_module
from pathlib import Path


def _auth_env(tmp_path: Path) -> dict[str, str]:
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path / "runtime"),
        "AIGNT_OS_RUNS_DB_PATH": str(tmp_path / "runs" / "runs.sqlite3"),
        "AIGNT_OS_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
        "AIGNT_OS_AUTH_ENABLED": "true",
    }


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F30-integration
type: feature
summary: Fixture spec for auth registry integration tests.
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


def _extract_value(output: str, label: str) -> str:
    prefix = f"{label}: "
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise AssertionError(f"Expected label '{label}' in output: {output}")


def test_auth_init_creates_registry_and_prints_token_once(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    auth_module = import_module("aignt_os.auth")

    result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=_auth_env(tmp_path),
    )

    registry_path = tmp_path / "runtime" / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    token = _extract_value(result.stdout, "Auth Token")
    token_id = _extract_value(result.stdout, "Token ID")

    assert result.exit_code == 0
    assert registry_path.exists()
    assert token
    assert token_id
    assert store.authenticate(token) is not None


def test_auth_init_fails_when_registry_already_exists(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    first_result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=_auth_env(tmp_path),
    )
    second_result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=_auth_env(tmp_path),
    )

    assert first_result.exit_code == 0
    assert second_result.exit_code == 5
    assert (
        "environment error:" in second_result.stdout.lower()
        or "environment error:" in second_result.stderr.lower()
    )


def test_auth_issue_creates_new_viewer_principal_when_role_is_provided(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    auth_module = import_module("aignt_os.auth")

    init_result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=_auth_env(tmp_path),
    )
    admin_token = _extract_value(init_result.stdout, "Auth Token")

    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = admin_token

    issue_result = cli_runner.invoke(
        cli_app,
        ["auth", "issue", "--principal-id", "viewer-user", "--role", "viewer"],
        env=env,
    )

    registry_path = tmp_path / "runtime" / "auth-registry.json"
    store = auth_module.AuthRegistryStore(registry_path)
    registry = store.load_registry()

    assert init_result.exit_code == 0
    assert issue_result.exit_code == 0
    assert any(principal.principal_id == "viewer-user" for principal in registry.principals)
    assert _extract_value(issue_result.stdout, "Principal ID") == "viewer-user"


def test_auth_issue_rejects_role_conflict_for_existing_principal(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    init_result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=_auth_env(tmp_path),
    )
    admin_token = _extract_value(init_result.stdout, "Auth Token")

    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = admin_token

    cli_runner.invoke(
        cli_app,
        ["auth", "issue", "--principal-id", "viewer-user", "--role", "viewer"],
        env=env,
    )

    result = cli_runner.invoke(
        cli_app,
        ["auth", "issue", "--principal-id", "viewer-user", "--role", "operator"],
        env=env,
    )

    assert result.exit_code == 2
    assert "usage error:" in result.stdout.lower() or "usage error:" in result.stderr.lower()


def test_auth_disable_revokes_token_used_by_runs_submit(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    init_result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=_auth_env(tmp_path),
    )
    admin_token = _extract_value(init_result.stdout, "Auth Token")

    env = _auth_env(tmp_path)
    env["AIGNT_OS_AUTH_TOKEN"] = admin_token

    issue_result = cli_runner.invoke(
        cli_app,
        ["auth", "issue", "--principal-id", "local-operator"],
        env=env,
    )
    token = _extract_value(issue_result.stdout, "Auth Token")
    token_id = _extract_value(issue_result.stdout, "Token ID")

    disable_result = cli_runner.invoke(
        cli_app,
        ["auth", "disable", "--token-id", token_id],
        env=env,  # Use env with admin token
    )

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    submit_env = _auth_env(tmp_path)
    submit_env["AIGNT_OS_AUTH_TOKEN"] = token
    submit_result = cli_runner.invoke(
        cli_app,
        ["runs", "submit", str(spec_path), "--mode", "sync", "--stop-at", "SPEC_VALIDATION"],
        env=submit_env,
    )

    assert disable_result.exit_code == 0
    assert submit_result.exit_code == 7
    assert (
        "authentication error:" in submit_result.stdout.lower()
        or "authentication error:" in submit_result.stderr.lower()
    )


def test_auth_init_rejects_state_dir_outside_workspace_root(
    tmp_path: Path,
    cli_runner,
    cli_app,
) -> None:
    env = _auth_env(tmp_path)
    env["AIGNT_OS_WORKSPACE_ROOT"] = str(tmp_path / "workspace")
    env["AIGNT_OS_RUNTIME_STATE_DIR"] = str(tmp_path / "outside-runtime")

    result = cli_runner.invoke(
        cli_app,
        ["auth", "init", "--principal-id", "local-operator"],
        env=env,
    )

    assert result.exit_code == 5
    assert (
        "environment error:" in result.stdout.lower()
        or "environment error:" in result.stderr.lower()
    )
    assert "trusted root" in result.stdout.lower() or "trusted root" in result.stderr.lower()
