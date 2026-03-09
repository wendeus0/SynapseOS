from __future__ import annotations

from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(REPO_ROOT / args[0]), *args[1:]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


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


def test_docker_rebuild_lists_relevant_inputs() -> None:
    result = run_script("scripts/docker-rebuild.sh", "--print-files")

    assert result.returncode == 0
    assert "pyproject.toml" in result.stdout
    assert "src/aignt_os/cli/app.py" in result.stdout
    assert "uv.lock" in result.stdout
