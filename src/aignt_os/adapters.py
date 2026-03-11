from __future__ import annotations

import asyncio
import re
import time
from abc import ABC, abstractmethod

from aignt_os.contracts import CLIExecutionResult

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class BaseCLIAdapter(ABC):
    def __init__(self, *, tool_name: str, timeout_seconds: float = 30.0) -> None:
        if not tool_name.strip():
            raise ValueError("tool_name must not be empty.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")

        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def build_command(self, prompt: str) -> list[str]:
        raise NotImplementedError

    async def execute(self, prompt: str) -> CLIExecutionResult:
        command = self.build_command(prompt)
        self._validate_command(command)

        started_at = time.monotonic()
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

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
        return ANSI_ESCAPE_RE.sub("", value).strip()

    def _validate_command(self, command: list[str]) -> None:
        if not command:
            raise ValueError("build_command() must return at least one token.")
        if any(not token.strip() for token in command):
            raise ValueError("build_command() returned an empty command token.")
