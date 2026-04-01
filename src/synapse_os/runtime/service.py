from __future__ import annotations

import errno
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from synapse_os.runtime.circuit_breaker import AdapterCircuitBreakerStore
from synapse_os.runtime.state import RuntimeState, RuntimeStateStore
from synapse_os.runtime.worker import RuntimeWorker

PROCESS_MARKER = "--synapse-runtime-process"


class RuntimeLifecycleEvent(BaseModel):
    model_config = ConfigDict(strict=True)

    event: str
    timestamp: float = Field(default_factory=time.time)
    data: dict[str, object] = Field(default_factory=dict)


def _runtime_process_code() -> str:
    return (
        "import signal\n"
        "import time\n"
        "running = True\n"
        "def handle_term(signum, frame):\n"
        "    global running\n"
        "    running = False\n"
        "signal.signal(signal.SIGTERM, handle_term)\n"
        "signal.signal(signal.SIGINT, handle_term)\n"
        "while running:\n"
        "    time.sleep(0.5)\n"
    )


class RuntimeService:
    def __init__(self, state_file: Path, *, worker: RuntimeWorker | None = None) -> None:
        self.state_store = RuntimeStateStore(state_file)
        self.worker = worker

    def start(self, *, started_by: str | None = None) -> RuntimeState:
        self._require_runnable_state()

        process_identity = secrets.token_hex(16)
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _runtime_process_code(),
                PROCESS_MARKER,
                process_identity,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(0.05)
        return self.state_store.write_running(
            process.pid,
            process_identity,
            started_by=started_by,
        )

    def status(self) -> RuntimeState:
        return self.current_state()

    def ready(self) -> bool:
        return self.current_state().status == "running"

    def run_foreground(self, process_identity: str, *, started_by: str | None = None) -> None:
        self._require_runnable_state()

        running = True

        def handle_shutdown(signum: int, frame: object) -> None:
            del signum, frame
            nonlocal running
            running = False

        previous_sigterm = signal.signal(signal.SIGTERM, handle_shutdown)
        previous_sigint = signal.signal(signal.SIGINT, handle_shutdown)

        self.state_store.write_running(
            os.getpid(),
            process_identity,
            started_by=started_by,
        )

        try:
            while running:
                if self.worker is None:
                    time.sleep(0.1)
                    continue

                processed_run_id = self.worker.poll_once()
                if processed_run_id is None:
                    self.worker.sleep_when_idle()
        finally:
            self.state_store.write_stopped()
            signal.signal(signal.SIGTERM, previous_sigterm)
            signal.signal(signal.SIGINT, previous_sigint)

    def stop(self) -> RuntimeState:
        state = self.current_state()
        if state.status == "inconsistent":
            raise RuntimeLifecycleError("Runtime state is inconsistent.")
        if state.status != "running" or state.pid is None:
            raise RuntimeLifecycleError("Runtime is not running.")

        self._stop_process(state.pid)
        return self.state_store.write_stopped()

    def current_state(self) -> RuntimeState:
        state = self.state_store.read()
        if state.status != "running" or state.pid is None:
            return state

        if not _pid_exists(state.pid) or not _process_identity_matches(
            state.pid, state.process_identity
        ):
            return RuntimeState(
                status="inconsistent",
                pid=state.pid,
                started_at=state.started_at,
                process_identity=state.process_identity,
                started_by=state.started_by,
            )
        return state

    def _require_runnable_state(self) -> None:
        state = self.current_state()
        if state.status == "running":
            raise RuntimeLifecycleError("Runtime is already running.")
        if state.status == "inconsistent":
            raise RuntimeLifecycleError("Runtime state is inconsistent.")

    def _stop_process(self, pid: int) -> None:
        deadline = time.monotonic() + 2.0
        os.kill(pid, signal.SIGTERM)
        while time.monotonic() < deadline:
            if not _pid_exists(pid):
                return
            time.sleep(0.05)

        os.kill(pid, signal.SIGKILL)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if not _pid_exists(pid):
                return
            time.sleep(0.05)


class RuntimeLifecycleError(RuntimeError):
    pass


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            return True
        raise
    return True


def _process_identity_matches(pid: int, process_identity: str | None) -> bool:
    if not process_identity:
        return False

    cmdline_path = Path("/proc") / str(pid) / "cmdline"
    try:
        arguments = cmdline_path.read_text(encoding="utf-8").split("\x00")
    except OSError:
        return False

    if PROCESS_MARKER in arguments and process_identity in arguments:
        return True

    return _is_foreground_runtime_process(arguments, process_identity)


def _is_foreground_runtime_process(arguments: list[str], process_identity: str) -> bool:
    return (
        "runtime" in arguments
        and "run" in arguments
        and "--process-identity" in arguments
        and process_identity in arguments
    )


class _InterruptibleHandler:
    def __init__(self, handler: Callable[[], None], timeout: float) -> None:
        self.handler = handler
        self.timeout = timeout
        self.thread: threading.Thread | None = None
        self.exc: BaseException | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            self.handler()
        except BaseException as e:
            self.exc = e

    def join(self, timeout: float) -> None:
        if self.thread is None:
            return
        self.thread.join(timeout=timeout)

    def cancel(self) -> None:
        pass

    def is_alive(self) -> bool:
        return self.thread is not None and self.thread.is_alive()


class RuntimeCoordinator:
    def __init__(
        self,
        circuit_breaker_store: AdapterCircuitBreakerStore | None = None,
    ) -> None:
        self.circuit_breaker_store = circuit_breaker_store or AdapterCircuitBreakerStore(
            Path(".synapse-os/runtime/circuit-breakers.json")
        )
        self.lifecycle_events: list[RuntimeLifecycleEvent] = []
        self._cleanup_handlers: list[Callable[[], None]] = []

    def health_status(self) -> Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]:
        open_adapters = [
            tool for tool in self._registered_tools() if self.circuit_breaker_store.is_open(tool)
        ]
        if not open_adapters:
            return "HEALTHY"
        if len(open_adapters) == 1:
            return "DEGRADED"
        return "UNHEALTHY"

    def lifecycle_event(self, event: str, data: dict[str, object] | None = None) -> None:
        self.lifecycle_events.append(RuntimeLifecycleEvent(event=event, data=data or {}))

    def register_cleanup_handler(self, handler: Callable[[], None]) -> None:
        self._cleanup_handlers.append(handler)

    def run_cleanup_handlers(self) -> None:
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception:
                pass

    def graceful_shutdown(self, timeout_seconds: float = 5.0) -> None:
        self.lifecycle_event("runtime.stopping")
        deadline = time.monotonic() + timeout_seconds
        remaining = timeout_seconds

        for handler in self._cleanup_handlers:
            if remaining <= 0:
                break
            thread = _InterruptibleHandler(handler, remaining)
            thread.start()
            thread.join(timeout=remaining)
            if thread.is_alive():
                thread.cancel()
            remaining = max(deadline - time.monotonic(), 0.0)

        self._stop()
        self.lifecycle_event("runtime.stopped")

    @property
    def degraded_adapters(self) -> set[str]:
        return {
            tool for tool in self._registered_tools() if self.circuit_breaker_store.is_open(tool)
        }

    def _registered_tools(self) -> list[str]:
        return ["codex", "gemini", "copilot"]

    def _stop(self) -> None:
        pass
