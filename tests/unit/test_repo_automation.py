from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(REPO_ROOT / args[0]), *args[1:]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_script_with_env(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(REPO_ROOT / args[0]), *args[1:]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_operational_ci_uses_real_pull_request_head_checkout() -> None:
    workflow_text = (REPO_ROOT / ".github/workflows/operational-ci.yml").read_text(encoding="utf-8")

    assert "ref: ${{ github.event.pull_request.head.sha }}" in workflow_text
    assert 'branch_name="$AIGNT_HEAD_REF"' in workflow_text


def test_operational_ci_repo_checks_use_sync_dev_commit_flow() -> None:
    workflow_text = (REPO_ROOT / ".github/workflows/operational-ci.yml").read_text(encoding="utf-8")

    assert "./scripts/commit-check.sh --sync-dev" in workflow_text
    assert "uv sync --locked --extra dev" not in workflow_text


def test_validate_branch_allows_current_branch_when_explicitly_permitted() -> None:
    result = run_script(
        "scripts/validate-branch.sh",
        "--base-ref",
        "origin/main",
        "--no-fetch",
        "--allow-main",
    )

    assert result.returncode == 0
    assert "aligned" in result.stdout


def test_validate_branch_uses_explicit_branch_name_override() -> None:
    result = run_script(
        "scripts/validate-branch.sh",
        "--base-ref",
        "origin/main",
        "--no-fetch",
        "--branch-name",
        "feature/test-branch",
    )

    assert result.returncode == 0
    assert "feature/test-branch" in result.stdout


def test_validate_commit_message_accepts_conventional_commit(tmp_path: Path) -> None:
    commit_message = tmp_path / "COMMIT_MSG"
    commit_message.write_text("feat(repo): add container automation\n", encoding="utf-8")

    result = run_script("scripts/validate-commit-message.sh", str(commit_message))

    assert result.returncode == 0
    assert "validated" in result.stdout


def test_validate_commit_message_rejects_invalid_pattern(tmp_path: Path) -> None:
    commit_message = tmp_path / "COMMIT_MSG"
    commit_message.write_text("automation update\n", encoding="utf-8")

    result = run_script("scripts/validate-commit-message.sh", str(commit_message))

    assert result.returncode != 0
    assert "conventional commit" in result.stderr.lower()


def test_docker_build_supports_dry_run() -> None:
    result = run_script("scripts/docker-build.sh", "--dry-run", "--tag", "aignt-os:test")

    assert result.returncode == 0
    assert "docker build" in result.stdout
    assert "aignt-os:test" in result.stdout
    assert str(REPO_ROOT / ".cache/docker/config") in result.stdout or result.stderr == ""


def test_docker_up_supports_dry_run() -> None:
    result = run_script("scripts/docker-up.sh", "--dry-run", "--build")

    assert result.returncode == 0
    assert "docker compose" in result.stdout
    assert "up" in result.stdout
    assert "--build" in result.stdout


def test_docker_preflight_supports_dry_run() -> None:
    result = run_script("scripts/docker-preflight.sh", "--dry-run")

    assert result.returncode == 0
    assert "docker compose" in result.stdout
    assert "config" in result.stdout
    assert "build" in result.stdout
    assert "up command" not in result.stdout


def test_docker_preflight_full_runtime_supports_dry_run() -> None:
    result = run_script("scripts/docker-preflight.sh", "--dry-run", "--full-runtime")

    assert result.returncode == 0
    assert "docker compose" in result.stdout
    assert "up command" in result.stdout
    assert "healthy" in result.stdout


def test_docker_preflight_full_runtime_requires_declared_healthcheck(
    tmp_path: Path, monkeypatch
) -> None:
    docker_bin = tmp_path / "docker"
    docker_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "version" ]]; then
  exit 0
fi
if [[ "$1" == "compose" ]]; then
  shift
  if [[ "$1" == "-f" ]]; then
    shift 2
  fi
  case "$1" in
    config|build|up)
      exit 0
      ;;
    ps)
      printf '%s\\n' fake-container-id
      exit 0
      ;;
  esac
fi
if [[ "$1" == "inspect" ]]; then
  if [[ "$3" == *".State.Status"* ]]; then
    printf '%s\\n' running
    exit 0
  fi
  if [[ "$3" == *".State.Health"* ]]; then
    printf '%s\\n' no-healthcheck
    exit 0
  fi
fi
echo "unexpected docker invocation: $*" >&2
exit 1
""",
        encoding="utf-8",
    )
    docker_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    monkeypatch.setenv("PATH", env["PATH"])

    result = run_script_with_env(
        env,
        "scripts/docker-preflight.sh",
        "--full-runtime",
        "--health-timeout",
        "1",
    )

    assert result.returncode != 0
    assert "healthcheck" in result.stderr.lower()


def test_docker_preflight_full_runtime_declares_runtime_health_gate() -> None:
    result = run_script("scripts/docker-preflight.sh", "--dry-run", "--full-runtime")

    assert result.returncode == 0
    assert "docker compose" in result.stdout
    assert "report healthy" in result.stdout


def test_docker_rebuild_lists_relevant_inputs() -> None:
    result = run_script("scripts/docker-rebuild.sh", "--print-files")

    assert result.returncode == 0
    assert "pyproject.toml" in result.stdout
    assert "src/aignt_os/cli/app.py" in result.stdout
    assert "uv.lock" in result.stdout


def test_security_gate_accepts_current_operational_surface() -> None:
    result = run_script("scripts/security-gate.sh")

    assert result.returncode == 0
    assert "Security gate passed" in result.stdout


def test_security_gate_falls_back_to_grep_when_rg_is_unavailable(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"

    result = run_script_with_env(env, "scripts/security-gate.sh")

    assert result.returncode == 0
    assert "Security gate passed" in result.stdout


def test_commit_check_hook_mode_skips_real_docker_preflight() -> None:
    result = run_script(
        "scripts/commit-check.sh",
        "--hook-mode",
        "--allow-main",
        "--skip-branch-validation",
        "--skip-format",
        "--skip-lint",
        "--skip-typecheck",
        "--skip-tests",
        "--skip-security",
    )

    assert result.returncode == 0
    assert "Light hook mode completed" in result.stdout


def test_commit_check_hook_mode_keeps_fast_no_sync_flow(tmp_path: Path, monkeypatch) -> None:
    uv_log = tmp_path / "uv.log"
    uv_bin = tmp_path / "uv"
    uv_bin.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$UV_LOG"\n',
        encoding="utf-8",
    )
    uv_bin.chmod(0o755)

    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("UV_LOG", str(uv_log))

    result = run_script(
        "scripts/commit-check.sh",
        "--hook-mode",
        "--allow-main",
        "--skip-branch-validation",
        "--skip-security",
    )

    assert result.returncode == 0
    assert "Resolved local validation flow: uv run --no-sync" in result.stdout

    uv_calls = uv_log.read_text(encoding="utf-8").splitlines()
    assert uv_calls == [
        "run --no-sync ruff format --check .",
        "run --no-sync ruff check .",
        "run --no-sync python -m mypy",
        "run --no-sync python -m pytest",
    ]


def test_commit_check_sync_dev_bootstraps_before_running_checks_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    uv_log = tmp_path / "uv.log"
    uv_bin = tmp_path / "uv"
    uv_bin.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$UV_LOG"\n',
        encoding="utf-8",
    )
    uv_bin.chmod(0o755)

    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("UV_LOG", str(uv_log))

    result = run_script(
        "scripts/commit-check.sh",
        "--allow-main",
        "--skip-branch-validation",
        "--skip-docker",
        "--skip-security",
    )

    assert result.returncode == 0
    assert "Resolved local validation flow: uv sync --locked --extra dev + uv run" in result.stdout

    uv_calls = uv_log.read_text(encoding="utf-8").splitlines()
    assert uv_calls == [
        "sync --locked --extra dev",
        "run ruff format --check .",
        "run ruff check .",
        "run python -m mypy",
        "run python -m pytest",
    ]


def test_commit_check_no_sync_keeps_fast_rerun_mode(tmp_path: Path, monkeypatch) -> None:
    uv_log = tmp_path / "uv.log"
    uv_bin = tmp_path / "uv"
    uv_bin.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$UV_LOG"\n',
        encoding="utf-8",
    )
    uv_bin.chmod(0o755)

    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("UV_LOG", str(uv_log))

    result = run_script(
        "scripts/commit-check.sh",
        "--no-sync",
        "--allow-main",
        "--skip-branch-validation",
        "--skip-docker",
        "--skip-security",
    )

    assert result.returncode == 0
    assert "Resolved local validation flow: uv run --no-sync" in result.stdout

    uv_calls = uv_log.read_text(encoding="utf-8").splitlines()
    assert uv_calls == [
        "run --no-sync ruff format --check .",
        "run --no-sync ruff check .",
        "run --no-sync python -m mypy",
        "run --no-sync python -m pytest",
    ]


def test_commit_check_blocks_before_sync_when_branch_validation_fails(
    tmp_path: Path, monkeypatch
) -> None:
    uv_log = tmp_path / "uv.log"
    uv_bin = tmp_path / "uv"
    uv_bin.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$UV_LOG"\n',
        encoding="utf-8",
    )
    uv_bin.chmod(0o755)

    git_bin = tmp_path / "git"
    git_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
args=("$@")
if [[ "${args[0]:-}" == "-C" ]]; then
  args=("${args[@]:2}")
fi
case "${args[*]}" in
  "rev-parse --verify origin/main")
    printf '%s\\n' fake-origin-main
    ;;
  "rev-parse --abbrev-ref HEAD")
    printf '%s\\n' main
    ;;
  *)
    echo "unexpected git invocation: ${args[*]}" >&2
    exit 1
    ;;
esac
""",
        encoding="utf-8",
    )
    git_bin.chmod(0o755)

    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("UV_LOG", str(uv_log))

    result = run_script(
        "scripts/commit-check.sh",
        "--skip-docker",
        "--skip-security",
    )

    assert result.returncode != 0
    assert "main" in result.stderr.lower()
    assert not uv_log.exists() or uv_log.read_text(encoding="utf-8") == ""


def test_compose_declares_runtime_healthcheck() -> None:
    compose_text = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert 'command: ["runtime", "run"]' in compose_text
    assert "healthcheck:" in compose_text
    assert 'test: ["CMD", "aignt", "runtime", "ready"]' in compose_text
