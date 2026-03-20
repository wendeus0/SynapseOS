from importlib import import_module

import pytest
from pydantic import ValidationError


def test_run_request_requires_non_empty_prompt() -> None:
    contracts_module = import_module("synapse_os.contracts")

    with pytest.raises(ValidationError):
        contracts_module.RunRequest(prompt="")


def test_run_request_serializes_to_plain_data() -> None:
    contracts_module = import_module("synapse_os.contracts")

    request = contracts_module.RunRequest(prompt="bootstrap project")

    assert request.model_dump() == {"prompt": "bootstrap project"}


@pytest.mark.parametrize(
    "prompt",
    [
        "a",
        "bootstrap project",
        "very long " * 100,
        "Prompt com acentuação: ã, é, ü",
        "   spaces around   ",
    ],
    ids=["single_char", "normal", "very_long", "unicode", "whitespace"],
)
def test_run_request_accepts_any_non_empty_prompt(prompt: str) -> None:
    contracts_module = import_module("synapse_os.contracts")

    request = contracts_module.RunRequest(prompt=prompt)

    assert request.prompt == prompt


def test_cli_execution_result_keeps_raw_and_clean_outputs_separate() -> None:
    contracts_module = import_module("synapse_os.contracts")

    result = contracts_module.CLIExecutionResult(
        tool_name="synapse",
        command=["synapse", "version"],
        return_code=0,
        stdout_raw="SynapseOS 0.1.0\n",
        stderr_raw="\u001b[31mwarn\u001b[0m\n",
        stdout_clean="SynapseOS 0.1.0",
        stderr_clean="warn",
        duration_ms=12,
        timed_out=False,
        success=True,
    )

    assert result.stdout_raw.endswith("\n")
    assert result.stdout_clean == "SynapseOS 0.1.0"
    assert result.stderr_raw.startswith("\u001b[31m")
    assert result.stderr_clean == "warn"
    assert result.duration_ms == 12
    assert result.model_dump()["command"] == ["synapse", "version"]


def test_cli_execution_result_rejects_invalid_return_code_type() -> None:
    contracts_module = import_module("synapse_os.contracts")

    with pytest.raises(ValidationError):
        contracts_module.CLIExecutionResult(
            tool_name="synapse",
            command=["synapse", "version"],
            return_code="0",
            stdout_raw="SynapseOS 0.1.0\n",
            stderr_raw="warn\n",
            stdout_clean="SynapseOS 0.1.0",
            stderr_clean="warn",
            duration_ms=12,
            timed_out=False,
            success=True,
        )


@pytest.mark.parametrize(
    "field_override, field_name",
    [
        ({"return_code": "0"}, "return_code"),
        ({"duration_ms": -1}, "duration_ms"),
        ({"duration_ms": 1.5}, "duration_ms"),
        ({"timed_out": "yes"}, "timed_out"),
        ({"success": 1}, "success"),
        ({"command": "synapse version"}, "command"),
    ],
    ids=[
        "return_code_as_string",
        "negative_duration",
        "float_duration",
        "timed_out_as_string",
        "success_as_int",
        "command_as_string_not_list",
    ],
)
def test_cli_execution_result_rejects_invalid_field_types(
    field_override: dict, field_name: str
) -> None:
    contracts_module = import_module("synapse_os.contracts")

    base = {
        "tool_name": "synapse",
        "command": ["synapse", "version"],
        "return_code": 0,
        "stdout_raw": "",
        "stderr_raw": "",
        "stdout_clean": "",
        "stderr_clean": "",
        "duration_ms": 10,
        "timed_out": False,
        "success": True,
    }
    base.update(field_override)

    with pytest.raises(ValidationError):
        contracts_module.CLIExecutionResult(**base)


def test_cli_execution_result_allows_timed_out_with_nonzero_return_code() -> None:
    contracts_module = import_module("synapse_os.contracts")

    result = contracts_module.CLIExecutionResult(
        tool_name="synapse",
        command=["synapse", "runtime", "run"],
        return_code=124,
        stdout_raw="",
        stderr_raw="timed out\n",
        stdout_clean="",
        stderr_clean="timed out",
        duration_ms=30000,
        timed_out=True,
        success=False,
    )

    assert result.timed_out is True
    assert result.return_code == 124
    assert result.success is False


def test_cli_execution_result_allows_zero_duration() -> None:
    contracts_module = import_module("synapse_os.contracts")

    result = contracts_module.CLIExecutionResult(
        tool_name="synapse",
        command=["synapse", "version"],
        return_code=0,
        stdout_raw="",
        stderr_raw="",
        stdout_clean="",
        stderr_clean="",
        duration_ms=0,
        timed_out=False,
        success=True,
    )

    assert result.duration_ms == 0


def test_tool_spec_requires_non_empty_capabilities() -> None:
    contracts_module = import_module("synapse_os.contracts")

    with pytest.raises(ValidationError):
        contracts_module.ToolSpec(
            name="codex",
            capabilities=(),
            command_prefix=("./scripts/dev-codex.sh",),
        )


def test_tool_spec_serializes_capabilities_and_command_prefix() -> None:
    contracts_module = import_module("synapse_os.contracts")

    tool_spec = contracts_module.ToolSpec(
        name="codex",
        capabilities=("cli_execution", "code_generation"),
        command_prefix=("./scripts/dev-codex.sh", "--", "exec"),
    )

    assert tool_spec.model_dump() == {
        "name": "codex",
        "capabilities": ("cli_execution", "code_generation"),
        "command_prefix": ("./scripts/dev-codex.sh", "--", "exec"),
    }
