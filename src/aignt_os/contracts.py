from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr


class RunRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1)]


class CLIExecutionResult(BaseModel):
    model_config = ConfigDict(strict=True)

    command: list[StrictStr]
    return_code: StrictInt
    stdout_raw: StrictStr
    stdout_clean: StrictStr
    success: StrictBool

