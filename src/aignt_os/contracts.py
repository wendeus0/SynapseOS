from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    StrictBool,
    StrictInt,
    StrictStr,
)


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
