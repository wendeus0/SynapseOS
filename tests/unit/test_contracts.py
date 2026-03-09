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
        command=["aignt", "version"],
        return_code=0,
        stdout_raw="AIgnt OS 0.1.0\n",
        stdout_clean="AIgnt OS 0.1.0",
        success=True,
    )

    assert result.stdout_raw.endswith("\n")
    assert result.stdout_clean == "AIgnt OS 0.1.0"
    assert result.model_dump()["command"] == ["aignt", "version"]


def test_cli_execution_result_rejects_invalid_return_code_type() -> None:
    contracts_module = import_module("aignt_os.contracts")

    with pytest.raises(ValidationError):
        contracts_module.CLIExecutionResult(
            command=["aignt", "version"],
            return_code="0",
            stdout_raw="AIgnt OS 0.1.0\n",
            stdout_clean="AIgnt OS 0.1.0",
            success=True,
        )
