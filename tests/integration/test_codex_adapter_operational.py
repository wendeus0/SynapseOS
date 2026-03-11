from __future__ import annotations

import asyncio
import os
from importlib import import_module
from pathlib import Path

import pytest


def _make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _install_fake_docker(tmp_path: Path, script_body: str) -> Path:
    docker_bin = tmp_path / "docker"
    _make_executable(
        docker_bin,
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                script_body,
                "",
            ]
        ),
    )
    return docker_bin


def test_codex_cli_adapter_executes_real_launcher_with_fake_docker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = import_module("aignt_os.adapters")
    fake_docker_log = tmp_path / "docker.log"

    _install_fake_docker(
        tmp_path,
        """
printf '%s\\n' "$*" >> "${FAKE_DOCKER_LOG:?}"
if [[ "$1" != "compose" ]]; then
  printf 'unexpected docker invocation: %s\\n' "$*" >&2
  exit 97
fi
shift
while [[ $# -gt 0 && "$1" == "-f" ]]; do
  shift 2
done
case "${1:-}" in
  up)
    exit 0
    ;;
  exec)
    printf 'codex smoke ok\\n'
    exit 0
    ;;
  *)
    printf 'unexpected compose subcommand: %s\\n' "${1:-}" >&2
    exit 98
    ;;
esac
""".strip(),
    )

    monkeypatch.setenv("FAKE_DOCKER_LOG", str(fake_docker_log))
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")

    result = asyncio.run(adapters.CodexCLIAdapter().execute("Implement the plan."))

    assert result.success is True
    assert result.tool_name == "codex"
    assert result.command == [
        "./scripts/dev-codex.sh",
        "--",
        "exec",
        "--color",
        "never",
        "Implement the plan.",
    ]
    assert "Resolved dev environment command:" in result.stdout_raw
    assert "Resolved Codex command:" in result.stdout_raw
    assert "codex smoke ok" in result.stdout_raw

    docker_log = fake_docker_log.read_text(encoding="utf-8")
    assert "up --detach codex-dev" in docker_log
    assert "exec -e CODEX_PROFILE=container_planning codex-dev bash -lc" in docker_log


def test_codex_cli_adapter_classifies_real_launcher_failure_with_fake_docker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = import_module("aignt_os.adapters")

    _install_fake_docker(
        tmp_path,
        """
if [[ "$1" != "compose" ]]; then
  printf 'unexpected docker invocation: %s\\n' "$*" >&2
  exit 97
fi
shift
while [[ $# -gt 0 && "$1" == "-f" ]]; do
  shift 2
done
if [[ "${1:-}" == "up" ]]; then
  printf 'Cannot connect to the Docker daemon\\n' >&2
  exit 1
fi
printf 'unexpected compose subcommand: %s\\n' "${1:-}" >&2
exit 98
""".strip(),
    )

    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")

    result = asyncio.run(adapters.CodexCLIAdapter().execute("Implement the plan."))
    assessment = adapters.classify_codex_execution(result)

    assert result.success is False
    assert assessment.category == "launcher_unavailable"
    assert assessment.is_operational_block is True
