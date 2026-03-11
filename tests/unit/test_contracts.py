from importlib import import_module

import pytest
from pydantic import ValidationError


def test_run_request_requires_non_empty_prompt() -> None:
    contracts_module = import_module("aignt_os.contracts")

    with pytest.raises(ValidationError):
        contracts_module.RunRequest(prompt="")


def test_run_request_serializes_to_plain_data() -> None:
    contracts_module = import_module("aignt_os.contracts")

    request = contracts_module.RunRequest(prompt="bootstrap project")

    assert request.model_dump() == {"prompt": "bootstrap project"}


def test_cli_execution_result_keeps_raw_and_clean_outputs_separate() -> None:
    contracts_module = import_module("aignt_os.contracts")

    result = contracts_module.CLIExecutionResult(
        tool_name="aignt",
        command=["aignt", "version"],
        return_code=0,
        stdout_raw="AIgnt OS 0.1.0\n",
        stderr_raw="\u001b[31mwarn\u001b[0m\n",
        stdout_clean="AIgnt OS 0.1.0",
        stderr_clean="warn",
        duration_ms=12,
        timed_out=False,
        success=True,
    )

    assert result.stdout_raw.endswith("\n")
    assert result.stdout_clean == "AIgnt OS 0.1.0"
    assert result.stderr_raw.startswith("\u001b[31m")
    assert result.stderr_clean == "warn"
    assert result.duration_ms == 12
    assert result.model_dump()["command"] == ["aignt", "version"]


def test_cli_execution_result_rejects_invalid_return_code_type() -> None:
    contracts_module = import_module("aignt_os.contracts")

    with pytest.raises(ValidationError):
        contracts_module.CLIExecutionResult(
            tool_name="aignt",
            command=["aignt", "version"],
            return_code="0",
            stdout_raw="AIgnt OS 0.1.0\n",
            stderr_raw="warn\n",
            stdout_clean="AIgnt OS 0.1.0",
            stderr_clean="warn",
            duration_ms=12,
            timed_out=False,
            success=True,
        )
