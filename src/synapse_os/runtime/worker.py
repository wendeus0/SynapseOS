from __future__ import annotations

import time
from collections.abc import Callable

from synapse_os.config import AppSettings
from synapse_os.persistence import (
    ArtifactStore,
    PersistedPipelineRunner,
    RunRecord,
    RunRepository,
)
from synapse_os.runtime.state import RuntimeState, RuntimeStateStore
from synapse_os.state_machine import PipelineState

LEGACY_INITIATED_BY_VALUES = frozenset({"unknown", "system", "local_cli"})
RUNTIME_OWNER_SKIP_EVENT = "runtime_owner_skip"


class RuntimeWorker:
    def __init__(
        self,
        *,
        repository: RunRepository,
        runner: PersistedPipelineRunner,
        poll_interval_seconds: float = 0.5,
        runtime_state_provider: Callable[[], RuntimeState] | None = None,
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.poll_interval_seconds = poll_interval_seconds
        self.runtime_state_provider = runtime_state_provider

    def poll_once(self) -> str | None:
        while True:
            run_record = self._next_pending_run()
            if run_record is None:
                return None
            if not self.repository.acquire_lock(run_record.run_id):
                continue
            try:
                self.runner.run_existing(run_record.run_id, assume_locked=True)
            except Exception:
                # Failed runs are already persisted by the runner observer.
                pass
            return run_record.run_id

    def sleep_when_idle(self) -> None:
        time.sleep(self.poll_interval_seconds)

    def _next_pending_run(self) -> RunRecord | None:
        runtime_owner = self._runtime_owner()
        if runtime_owner is None:
            return self.repository.find_next_pending_run()
        compatible_initiators = set(LEGACY_INITIATED_BY_VALUES | {runtime_owner})
        for run_record in self.repository.list_unlocked_pending_runs():
            if run_record.initiated_by in compatible_initiators:
                return run_record
            self._record_owner_skip_if_needed(run_record, runtime_owner=runtime_owner)
        return None

    def _runtime_owner(self) -> str | None:
        if self.runtime_state_provider is None:
            return None

        runtime_state = self.runtime_state_provider()
        if runtime_state.status != "running" or runtime_state.started_by is None:
            return None

        return runtime_state.started_by

    def _record_owner_skip_if_needed(self, run_record: RunRecord, *, runtime_owner: str) -> None:
        message = (
            "Worker skipped pending run due to runtime ownership mismatch: "
            f"runtime_started_by={runtime_owner} run_initiated_by={run_record.initiated_by}."
        )
        latest_event = self.repository.get_latest_event(run_record.run_id)
        if (
            latest_event is not None
            and latest_event.event_type == RUNTIME_OWNER_SKIP_EVENT
            and latest_event.message == message
        ):
            return
        self.repository.record_event(
            run_record.run_id,
            state=PipelineState.REQUEST,
            event_type=RUNTIME_OWNER_SKIP_EVENT,
            message=message,
        )


def build_runtime_worker(settings: AppSettings) -> RuntimeWorker:
    repository = RunRepository(settings.runs_db_path_resolved)
    artifact_store = ArtifactStore(settings.artifacts_dir_resolved)
    runtime_state_store = RuntimeStateStore(settings.runtime_state_file)
    runner = PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    return RuntimeWorker(
        repository=repository,
        runner=runner,
        poll_interval_seconds=settings.runtime_poll_interval_seconds,
        runtime_state_provider=runtime_state_store.read if settings.auth_enabled else None,
    )
