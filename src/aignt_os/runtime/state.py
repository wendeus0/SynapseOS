from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PID_MAX = 4_194_304
STATE_DIR_MODE = 0o700
STATE_FILE_MODE = 0o600


@dataclass(slots=True)
class RuntimeState:
    status: str
    pid: int | None = None
    started_at: str | None = None
    process_identity: str | None = None


class RuntimeStateStore:
    def __init__(self, path: Path) -> None:
        if ".." in path.parts:
            raise ValueError("Invalid runtime state directory.")
        self.path = path

    def read(self) -> RuntimeState:
        if not self.path.exists():
            return RuntimeState(status="stopped")

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return RuntimeState(status="inconsistent")

        status = payload.get("status")
        pid = payload.get("pid")
        started_at = payload.get("started_at")
        process_identity = payload.get("process_identity")

        if status == "running":
            if (
                not isinstance(pid, int)
                or pid <= 0
                or pid > PID_MAX
                or not isinstance(process_identity, str)
                or not process_identity
            ):
                return RuntimeState(status="inconsistent")
            return RuntimeState(
                status="running",
                pid=pid,
                started_at=started_at,
                process_identity=process_identity,
            )

        if status == "stopped":
            return RuntimeState(status="stopped", pid=None, started_at=started_at)

        return RuntimeState(status="inconsistent")

    def write_running(self, pid: int, process_identity: str = "local-runtime") -> RuntimeState:
        state = RuntimeState(
            status="running",
            pid=pid,
            started_at=datetime.now(UTC).isoformat(),
            process_identity=process_identity,
        )
        self._write(state)
        return state

    def write_stopped(self) -> RuntimeState:
        state = RuntimeState(status="stopped")
        self._write(state)
        return state

    def _write(self, state: RuntimeState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)
        os.chmod(self.path.parent, STATE_DIR_MODE)

        payload = json.dumps(
            {
                "status": state.status,
                "pid": state.pid,
                "started_at": state.started_at,
                "process_identity": state.process_identity,
            }
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(payload)
            temporary_path = Path(temporary_file.name)

        os.chmod(temporary_path, STATE_FILE_MODE)
        os.replace(temporary_path, self.path)
        os.chmod(self.path, STATE_FILE_MODE)
