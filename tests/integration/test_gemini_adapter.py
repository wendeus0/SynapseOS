from __future__ import annotations

import asyncio
from importlib import import_module
from pathlib import Path

import pytest


def test_gemini_adapter_executes_with_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = import_module("synapse_os.adapters")

    monkeypatch.setenv("SYNAPSE_OS_GEMINI_API_KEY", "fake-key")

    adapter = adapters.GeminiCLIAdapter()
    result = asyncio.run(adapter.execute("Hello World"))

    assert result.success is True
    assert result.tool_name == "gemini"
    assert "Gemini response to: Hello World" in result.stdout_clean
    assert result.return_code == 0


def test_gemini_adapter_fails_without_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapters = import_module("synapse_os.adapters")

    monkeypatch.delenv("SYNAPSE_OS_GEMINI_API_KEY", raising=False)

    adapter = adapters.GeminiCLIAdapter()
    result = asyncio.run(adapter.execute("Hello World"))

    assert result.success is False
    assert result.tool_name == "gemini"
    assert "Error: SYNAPSE_OS_GEMINI_API_KEY not set" in result.stderr_clean
    assert result.return_code != 0
