from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aignt_os.persistence import PersistedPipelineRunner, RunRepository
from aignt_os.runtime.state import RuntimeState
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


class AsyncDispatchRuntimeUnavailableError(RuntimeError):
    pass


class AsyncDispatchOwnershipError(RuntimeError):
    pass


class RunDispatchService:
    def __init__(
        self,
        *,
        repository: RunRepository,
        runner: PersistedPipelineRunner,
        is_runtime_ready: Callable[[], bool],
        workspace_root: Path,
        initiated_by: str = "local_cli",
        runtime_state_provider: Callable[[], RuntimeState] | None = None,
        enforce_async_runtime_ownership: bool = False,
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.is_runtime_ready = is_runtime_ready
        self.workspace_root = workspace_root
        self.initiated_by = initiated_by
        self.runtime_state_provider = runtime_state_provider
        self.enforce_async_runtime_ownership = enforce_async_runtime_ownership

    def dispatch(
        self,
        spec_path: Path,
        *,
        stop_at: str = "TEST_RED",
        mode: DispatchMode = "auto",
    ) -> RunDispatchResult:
        resolved_spec_path = self._validate_dispatch_inputs(spec_path, mode=mode)
        resolved_mode = self._resolve_mode(mode)
        self._authorize_async_dispatch(resolved_mode)
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

    def _authorize_async_dispatch(self, resolved_mode: ResolvedDispatchMode) -> None:
        if resolved_mode != "async" or not self.enforce_async_runtime_ownership:
            return

        runtime_state = self._runtime_state()
        if runtime_state.status != "running":
            raise AsyncDispatchRuntimeUnavailableError(
                "Authenticated async dispatch requires a running resident runtime."
            )
        if runtime_state.started_by is None:
            return
        if self.initiated_by != runtime_state.started_by:
            raise AsyncDispatchOwnershipError(
                "Authenticated principal is not allowed to submit async work "
                "to a runtime started by another principal."
            )

    def _runtime_state(self) -> RuntimeState:
        if self.runtime_state_provider is None:
            return RuntimeState(status="stopped")
        return self.runtime_state_provider()
