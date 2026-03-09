from __future__ import annotations

import errno
import os
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path

from aignt_os.runtime.state import RuntimeState, RuntimeStateStore

PROCESS_MARKER = "--aignt-runtime-process"


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
    def __init__(self, state_file: Path) -> None:
        self.state_store = RuntimeStateStore(state_file)

    def start(self) -> RuntimeState:
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
        return self.state_store.write_running(process.pid, process_identity)

    def status(self) -> RuntimeState:
        return self.current_state()

    def ready(self) -> bool:
        return self.current_state().status == "running"

    def run_foreground(self, process_identity: str) -> None:
        self._require_runnable_state()

        running = True

        def handle_shutdown(signum: int, frame: object) -> None:
            del signum, frame
            nonlocal running
            running = False

        previous_sigterm = signal.signal(signal.SIGTERM, handle_shutdown)
        previous_sigint = signal.signal(signal.SIGINT, handle_shutdown)

        # This is the minimal resident process for the AIgnt-Synapse-Flow runtime.
        self.state_store.write_running(os.getpid(), process_identity)

        try:
            while running:
                time.sleep(0.1)
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
