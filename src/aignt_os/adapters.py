from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod

from aignt_os.config import AppSettings
from aignt_os.contracts import CLIExecutionResult, CodexExecutionAssessment
from aignt_os.security import sanitize_clean_text

_LAUNCHER_UNAVAILABLE_PATTERNS = (
    "docker: command not found",
    "cannot connect to the docker daemon",
    "failed to connect to the docker daemon",
)
_CONTAINER_UNAVAILABLE_PATTERNS = (
    "no such service",
    'service "codex-dev" is not running',
    "no such container",
)
_AUTHENTICATION_UNAVAILABLE_PATTERNS = (
    "authentication required",
    "not logged in",
    "unauthorized",
    "invalid token",
    "api key",
    "missing bearer or basic authentication",
)
_ADAPTER_EXECUTION_GUARDS: dict[int, asyncio.Semaphore] = {}


class AdapterOperationalError(RuntimeError):
    def __init__(
        self,
        *,
        tool_name: str,
        command: list[str],
        reason: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.tool_name = tool_name
        self.command = command
        self.reason = reason


class BaseCLIAdapter(ABC):
    def __init__(
        self,
        *,
        tool_name: str,
        timeout_seconds: float = 30.0,
        max_concurrent_adapters: int | None = None,
    ) -> None:
        if not tool_name.strip():
            raise ValueError("tool_name must not be empty.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")

        resolved_max_concurrent_adapters = (
            AppSettings().max_concurrent_adapters
            if max_concurrent_adapters is None
            else max_concurrent_adapters
        )
        if resolved_max_concurrent_adapters <= 0:
            raise ValueError("max_concurrent_adapters must be positive.")

        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        self.max_concurrent_adapters = resolved_max_concurrent_adapters

    @abstractmethod
    def build_command(self, prompt: str) -> list[str]:
        raise NotImplementedError

    async def execute(self, prompt: str) -> CLIExecutionResult:
        command = self.build_command(prompt)
        self._validate_command(command)

        async with _execution_guard(self.max_concurrent_adapters):
            started_at = time.monotonic()
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            except OSError as exc:
                raise AdapterOperationalError(
                    tool_name=self.tool_name,
                    command=command,
                    reason="launcher_unavailable",
                    message=(
                        f"{self.tool_name} launcher unavailable for command {command!r}: {exc}"
                    ),
                ) from exc

            timed_out = False
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
            except TimeoutError:
                timed_out = True
                process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()

            duration_ms = max(0, int((time.monotonic() - started_at) * 1000))
            return_code = process.returncode if process.returncode is not None else -1
            stdout_raw = stdout_bytes.decode("utf-8", errors="replace")
            stderr_raw = stderr_bytes.decode("utf-8", errors="replace")

            return CLIExecutionResult(
                tool_name=self.tool_name,
                command=command,
                return_code=return_code,
                stdout_raw=stdout_raw,
                stderr_raw=stderr_raw,
                stdout_clean=self._sanitize_stream(stdout_raw),
                stderr_clean=self._sanitize_stream(stderr_raw),
                duration_ms=duration_ms,
                timed_out=timed_out,
                success=not timed_out and return_code == 0,
            )

    def _sanitize_stream(self, value: str) -> str:
        return sanitize_clean_text(
            value,
            remove_ansi=True,
            strip_outer_whitespace=True,
        )

    def _validate_command(self, command: list[str]) -> None:
        if not command:
            raise ValueError("build_command() must return at least one token.")
        if any(not token.strip() for token in command):
            raise ValueError("build_command() returned an empty command token.")


class CodexCLIAdapter(BaseCLIAdapter):
    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        max_concurrent_adapters: int | None = None,
    ) -> None:
        super().__init__(
            tool_name="codex",
            timeout_seconds=timeout_seconds,
            max_concurrent_adapters=max_concurrent_adapters,
        )

    def build_command(self, prompt: str) -> list[str]:
        if not prompt.strip():
            raise ValueError("prompt must not be empty.")
        return [
            "./scripts/dev-codex.sh",
            "--",
            "exec",
            "--color",
            "never",
            prompt,
        ]


def classify_codex_execution(result: CLIExecutionResult) -> CodexExecutionAssessment:
    stderr_lower = result.stderr_clean.lower()

    if result.success:
        return CodexExecutionAssessment(
            category="success",
            is_operational_block=False,
            detail="Codex CLI completed successfully.",
        )
    if result.timed_out:
        return CodexExecutionAssessment(
            category="timeout",
            is_operational_block=False,
            detail="Codex CLI exceeded the configured timeout.",
        )
    if _contains_any(stderr_lower, _LAUNCHER_UNAVAILABLE_PATTERNS):
        return CodexExecutionAssessment(
            category="launcher_unavailable",
            is_operational_block=True,
            detail=result.stderr_clean or "Codex launcher or Docker runtime is unavailable.",
        )
    if _contains_any(stderr_lower, _CONTAINER_UNAVAILABLE_PATTERNS):
        return CodexExecutionAssessment(
            category="container_unavailable",
            is_operational_block=True,
            detail=result.stderr_clean or "Codex container is unavailable.",
        )
    if _contains_any(stderr_lower, _AUTHENTICATION_UNAVAILABLE_PATTERNS):
        return CodexExecutionAssessment(
            category="authentication_unavailable",
            is_operational_block=True,
            detail=result.stderr_clean or "Codex authentication is unavailable.",
        )
    return CodexExecutionAssessment(
        category="return_code_nonzero",
        is_operational_block=False,
        detail=result.stderr_clean or "Codex CLI exited with a non-zero return code.",
    )


def _contains_any(value: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in value for pattern in patterns)


def _execution_guard(limit: int) -> asyncio.Semaphore:
    guard = _ADAPTER_EXECUTION_GUARDS.get(limit)
    if guard is None:
        guard = asyncio.Semaphore(limit)
        _ADAPTER_EXECUTION_GUARDS[limit] = guard
    return guard
