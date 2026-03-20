from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    StrictBool,
    StrictInt,
    StrictStr,
)

from synapse_os.runtime_contracts import ToolSpec

__all__ = [
    "RunRequest",
    "CLIExecutionResult",
    "CodexExecutionAssessment",
    "ToolSpec",
]


class RunRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1)]


class CLIExecutionResult(BaseModel):
    model_config = ConfigDict(strict=True)

    tool_name: StrictStr
    command: list[StrictStr]
    return_code: StrictInt
    stdout_raw: StrictStr
    stderr_raw: StrictStr
    stdout_clean: StrictStr
    stderr_clean: StrictStr
    duration_ms: NonNegativeInt
    timed_out: StrictBool
    success: StrictBool


class CodexExecutionAssessment(BaseModel):
    model_config = ConfigDict(strict=True)

    category: Literal[
        "success",
        "timeout",
        "return_code_nonzero",
        "circuit_open",
        "launcher_unavailable",
        "container_unavailable",
        "authentication_unavailable",
    ]
    is_operational_block: StrictBool
    detail: StrictStr
