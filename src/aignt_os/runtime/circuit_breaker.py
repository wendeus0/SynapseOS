from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from aignt_os.runtime.state import STATE_DIR_MODE, STATE_FILE_MODE


@dataclass(frozen=True, slots=True)
class CircuitBreakerState:
    tool_name: str
    consecutive_operational_failures: int
    opened_at: float | None = None
    cooldown_until: float | None = None


class AdapterCircuitBreakerStore:
    def __init__(self, path: Path) -> None:
        if ".." in path.parts:
            raise ValueError("Invalid circuit breaker state directory.")
        self.path = path

    def read(self, tool_name: str) -> CircuitBreakerState | None:
        payload = self._load_payload()
        state_payload = payload.get(tool_name)
        if not isinstance(state_payload, dict):
            return None

        failures = state_payload.get("consecutive_operational_failures")
        opened_at = state_payload.get("opened_at")
        cooldown_until = state_payload.get("cooldown_until")
        if not isinstance(failures, int) or failures <= 0:
            return None
        if opened_at is not None and not isinstance(opened_at, (int, float)):
            return None
        if cooldown_until is not None and not isinstance(cooldown_until, (int, float)):
            return None

        return CircuitBreakerState(
            tool_name=tool_name,
            consecutive_operational_failures=failures,
            opened_at=float(opened_at) if opened_at is not None else None,
            cooldown_until=float(cooldown_until) if cooldown_until is not None else None,
        )

    def is_open(self, tool_name: str, *, now: float | None = None) -> bool:
        state = self.read(tool_name)
        if state is None or state.cooldown_until is None:
            return False
        current_time = _current_time(now)
        return current_time < state.cooldown_until

    def record_operational_failure(
        self,
        tool_name: str,
        *,
        threshold: int,
        cooldown_seconds: float,
        now: float | None = None,
    ) -> CircuitBreakerState:
        current_time = _current_time(now)
        current_state = self.read(tool_name)
        failure_count = 1
        if current_state is not None:
            failure_count = current_state.consecutive_operational_failures + 1

        opened_at: float | None = None
        cooldown_until: float | None = None
        if failure_count >= threshold:
            opened_at = current_time
            cooldown_until = current_time + cooldown_seconds

        new_state = CircuitBreakerState(
            tool_name=tool_name,
            consecutive_operational_failures=failure_count,
            opened_at=opened_at,
            cooldown_until=cooldown_until,
        )
        payload = self._load_payload()
        payload[tool_name] = asdict(new_state)
        self._write_payload(payload)
        return new_state

    def reset(self, tool_name: str) -> None:
        payload = self._load_payload()
        if tool_name not in payload:
            return
        del payload[tool_name]
        self._write_payload(payload)

    def _load_payload(self) -> dict[str, dict[str, object]]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            key: value
            for key, value in payload.items()
            if isinstance(key, str) and isinstance(value, dict)
        }

    def _write_payload(self, payload: dict[str, dict[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)
        os.chmod(self.path.parent, STATE_DIR_MODE)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(json.dumps(payload))
            temporary_path = Path(temporary_file.name)

        os.chmod(temporary_path, STATE_FILE_MODE)
        os.replace(temporary_path, self.path)
        os.chmod(self.path, STATE_FILE_MODE)


def _current_time(now: float | None) -> float:
    if now is None:
        import time

        return time.time()
    return now
