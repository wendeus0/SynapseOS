"""Shared fixtures for integration tests."""

from __future__ import annotations

import os
import sys
from importlib import import_module
from pathlib import Path

import pytest
from typer.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def cli_runner() -> CliRunner:
    """Return a Typer CliRunner for invoking CLI commands in tests."""
    return CliRunner()


@pytest.fixture()
def cli_app():
    """Return the main Typer app."""
    return import_module("aignt_os.cli.app").app


@pytest.fixture()
def runtime_env(tmp_path: Path) -> dict[str, str]:
    """Return environment variables pointing the runtime to a temporary directory."""
    return {
        "AIGNT_OS_ENVIRONMENT": "test",
        "AIGNT_OS_RUNTIME_STATE_DIR": str(tmp_path),
        "AIGNT_OS_WORKSPACE_ROOT": str(tmp_path),
    }


@pytest.fixture()
def subprocess_env(tmp_path: Path) -> dict[str, str]:
    """Return a full os.environ copy with runtime overrides for subprocess spawning."""
    env = os.environ.copy()
    python_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{python_path}{os.pathsep}{existing}" if existing else python_path
    env["AIGNT_OS_ENVIRONMENT"] = "test"
    env["AIGNT_OS_RUNTIME_STATE_DIR"] = str(tmp_path)
    env["AIGNT_OS_WORKSPACE_ROOT"] = str(tmp_path)
    return env


@pytest.fixture()
def python_executable() -> str:
    """Return the current Python interpreter path."""
    return sys.executable
