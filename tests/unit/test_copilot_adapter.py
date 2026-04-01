from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from synapse_os.adapters import (
    CopilotCLIAdapter,
    CLIExecutionResult,
    classify_copilot_execution,
)


class TestCopilotCLIAdapter:
    def test_capabilities(self) -> None:
        adapter = CopilotCLIAdapter()
        assert adapter.capabilities == ("cli_execution", "code_generation")

    def test_tool_spec_name(self) -> None:
        adapter = CopilotCLIAdapter()
        assert adapter.tool_spec.name == "copilot"

    def test_build_command(self) -> None:
        adapter = CopilotCLIAdapter()
        cmd = adapter.build_command("write a hello world in python")
        assert "gh" in cmd
        assert "copilot" in cmd
        assert "write a hello world in python" in cmd

    def test_build_command_empty_prompt_raises(self) -> None:
        adapter = CopilotCLIAdapter()
        with pytest.raises(ValueError, match="empty"):
            adapter.build_command("   ")


class TestClassifyCopilotExecution:
    def test_success(self) -> None:
        result = CLIExecutionResult(
            tool_name="copilot",
            command=["gh", "copilot", "ai"],
            return_code=0,
            stdout_raw="def hello(): pass\n",
            stderr_raw="",
            stdout_clean="def hello(): pass\n",
            stderr_clean="",
            duration_ms=500,
            timed_out=False,
            success=True,
        )
        assessment = classify_copilot_execution(result)
        assert assessment.category == "success"
        assert not assessment.is_operational_block

    def test_timeout(self) -> None:
        result = CLIExecutionResult(
            tool_name="copilot",
            command=["gh", "copilot", "ai"],
            return_code=-1,
            stdout_raw="",
            stderr_raw="",
            stdout_clean="",
            stderr_clean="",
            duration_ms=30000,
            timed_out=True,
            success=False,
        )
        assessment = classify_copilot_execution(result)
        assert assessment.category == "timeout"
        assert not assessment.is_operational_block

    def test_return_code_nonzero(self) -> None:
        result = CLIExecutionResult(
            tool_name="copilot",
            command=["gh", "copilot", "ai"],
            return_code=1,
            stdout_raw="",
            stderr_raw="Something went wrong.",
            stdout_clean="",
            stderr_clean="Something went wrong.",
            duration_ms=200,
            timed_out=False,
            success=False,
        )
        assessment = classify_copilot_execution(result)
        assert assessment.category == "return_code_nonzero"
        assert not assessment.is_operational_block

    def test_authentication_unavailable(self) -> None:
        result = CLIExecutionResult(
            tool_name="copilot",
            command=["gh", "copilot", "ai"],
            return_code=1,
            stdout_raw="",
            stderr_raw="Error: authenticated required",
            stdout_clean="",
            stderr_clean="Error: authenticated required",
            duration_ms=100,
            timed_out=False,
            success=False,
        )
        assessment = classify_copilot_execution(result)
        assert assessment.category == "authentication_unavailable"
        assert assessment.is_operational_block

    def test_launcher_unavailable(self) -> None:
        result = CLIExecutionResult(
            tool_name="copilot",
            command=["gh", "copilot", "ai"],
            return_code=127,
            stdout_raw="",
            stderr_raw="gh: command not found",
            stdout_clean="",
            stderr_clean="gh: command not found",
            duration_ms=50,
            timed_out=False,
            success=False,
        )
        assessment = classify_copilot_execution(result)
        assert assessment.category == "launcher_unavailable"
        assert assessment.is_operational_block

    def test_circuit_open(self) -> None:
        result = CLIExecutionResult(
            tool_name="copilot",
            command=["gh", "copilot", "ai"],
            return_code=75,
            stdout_raw="",
            stderr_raw="circuit breaker open for copilot.\n",
            stdout_clean="",
            stderr_clean="circuit breaker open for copilot.",
            duration_ms=0,
            timed_out=False,
            success=False,
        )
        assessment = classify_copilot_execution(result)
        assert assessment.category == "circuit_open"
        assert assessment.is_operational_block
