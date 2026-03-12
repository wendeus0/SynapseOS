from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aignt_os.persistence import PersistedPipelineRunner, RunRepository
from aignt_os.security import compute_file_sha256, resolve_path_within_root
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
        workspace_root: Path,
        initiated_by: str = "local_cli",
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.is_runtime_ready = is_runtime_ready
        self.workspace_root = workspace_root
        self.initiated_by = initiated_by

    def dispatch(
        self,
        spec_path: Path,
        *,
        stop_at: str = "TEST_RED",
        mode: DispatchMode = "auto",
    ) -> RunDispatchResult:
        resolved_spec_path = self._validate_dispatch_inputs(spec_path, mode=mode)
        resolved_mode = self._resolve_mode(mode)
        if resolved_mode == "sync":
            context = self.runner.run(
                resolved_spec_path,
                stop_at=stop_at,
                initiated_by=self.initiated_by,
                spec_hash=compute_file_sha256(resolved_spec_path),
            )
            if context.run_id is None:
                raise RuntimeError("Synchronous dispatch completed without a run_id.")
            return RunDispatchResult(
                run_id=context.run_id,
                status="completed",
                dispatch_mode_resolved="sync",
            )

        run_id = self.runner.create_pending_run(
            resolved_spec_path,
            stop_at=stop_at,
            initiated_by=self.initiated_by,
            spec_hash=compute_file_sha256(resolved_spec_path),
        )
        return RunDispatchResult(
            run_id=run_id,
            status="queued",
            dispatch_mode_resolved="async",
        )

    def _validate_dispatch_inputs(self, spec_path: Path, *, mode: DispatchMode) -> Path:
        self._resolve_mode(mode)
        try:
            resolved_spec_path = resolve_path_within_root(spec_path, root=self.workspace_root)
        except ValueError as exc:
            raise FileNotFoundError(f"SPEC file not found: {spec_path}") from exc
        if not resolved_spec_path.exists():
            raise FileNotFoundError(f"SPEC file not found: {spec_path}")
        if not resolved_spec_path.is_file():
            raise FileNotFoundError(f"SPEC file not found: {spec_path}")
        validate_spec_file(resolved_spec_path)
        return resolved_spec_path

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
