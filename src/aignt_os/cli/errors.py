from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import NoReturn

import typer


class CLIExitCode(IntEnum):
    SUCCESS = 0
    USAGE = 2
    NOT_FOUND = 3
    VALIDATION = 4
    ENVIRONMENT = 5
    EXECUTION = 6
    AUTHENTICATION = 7
    AUTHORIZATION = 8


@dataclass(frozen=True, slots=True)
class CLIError(Exception):
    exit_code: CLIExitCode
    detail: str

    def __str__(self) -> str:
        return format_cli_error(self.exit_code, self.detail)


def format_cli_error(exit_code: CLIExitCode, detail: str) -> str:
    return f"{_error_prefix(exit_code)}: {detail}"


def exit_for_cli_error(error: CLIError) -> NoReturn:
    typer.echo(str(error), err=True)
    raise typer.Exit(code=int(error.exit_code))


def usage_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.USAGE, detail)


def not_found_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.NOT_FOUND, detail)


def validation_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.VALIDATION, detail)


def environment_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.ENVIRONMENT, detail)


def execution_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.EXECUTION, detail)


def authentication_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.AUTHENTICATION, detail)


def authorization_error(detail: str) -> CLIError:
    return CLIError(CLIExitCode.AUTHORIZATION, detail)


def _error_prefix(exit_code: CLIExitCode) -> str:
    if exit_code == CLIExitCode.USAGE:
        return "Usage error"
    if exit_code == CLIExitCode.NOT_FOUND:
        return "Not found"
    if exit_code == CLIExitCode.VALIDATION:
        return "Validation error"
    if exit_code == CLIExitCode.ENVIRONMENT:
        return "Environment error"
    if exit_code == CLIExitCode.EXECUTION:
        return "Execution error"
    if exit_code == CLIExitCode.AUTHENTICATION:
        return "Authentication error"
    if exit_code == CLIExitCode.AUTHORIZATION:
        return "Authorization error"
    return "CLI error"
