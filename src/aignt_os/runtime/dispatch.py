from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aignt_os.persistence import PersistedPipelineRunner, RunRepository
from aignt_os.specs import validate_spec_file

DispatchMode = Literal["sync", "async", "auto"]
ResolvedDispatchMode = Literal["sync", "async"]
DispatchStatus = Literal["queued", "completed"]


@dataclass(frozen=True, slots=True)
class RunDispatchResult:
    run_id: str
    status: DispatchStatus
    dispatch_mode_resolved: ResolvedDispatchMode


class RunDispatchService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        runner: PersistedPipelineRunner,
        is_runtime_ready: Callable[[], bool],
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.is_runtime_ready = is_runtime_ready

    def dispatch(
        self,
        spec_path: Path,
        *,
        stop_at: str = "TEST_RED",
        mode: DispatchMode = "auto",
    ) -> RunDispatchResult:
        self._validate_dispatch_inputs(spec_path, mode=mode)
        resolved_mode = self._resolve_mode(mode)
        if resolved_mode == "sync":
            context = self.runner.run(spec_path, stop_at=stop_at)
            if context.run_id is None:
                raise RuntimeError("Synchronous dispatch completed without a run_id.")
            return RunDispatchResult(
                run_id=context.run_id,
                status="completed",
                dispatch_mode_resolved="sync",
            )

        run_id = self.runner.create_pending_run(spec_path, stop_at=stop_at)
        return RunDispatchResult(
            run_id=run_id,
            status="queued",
            dispatch_mode_resolved="async",
        )

    def _validate_dispatch_inputs(self, spec_path: Path, *, mode: DispatchMode) -> None:
        if not spec_path.exists():
            raise FileNotFoundError(f"SPEC file not found: {spec_path}")
        if not spec_path.is_file():
            raise ValueError(f"SPEC path is not a file: {spec_path}")

        self._resolve_mode(mode)
        validate_spec_file(spec_path)

    def _resolve_mode(self, mode: DispatchMode) -> ResolvedDispatchMode:
        if mode == "sync":
            return "sync"
        if mode == "async":
            return "async"
        if self.is_runtime_ready():
            return "async"
        if mode != "auto":
            raise ValueError(f"Unsupported dispatch mode: {mode}")
        return "sync"
