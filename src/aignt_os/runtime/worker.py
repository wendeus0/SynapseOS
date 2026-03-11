from __future__ import annotations

import time

from aignt_os.config import AppSettings
from aignt_os.persistence import ArtifactStore, PersistedPipelineRunner, RunRepository


class RuntimeWorker:
    def __init__(
        self,
        *,
        repository: RunRepository,
        runner: PersistedPipelineRunner,
        poll_interval_seconds: float = 0.5,
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.poll_interval_seconds = poll_interval_seconds

    def poll_once(self) -> str | None:
        while True:
            run_record = self.repository.find_next_pending_run()
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


def build_runtime_worker(settings: AppSettings) -> RuntimeWorker:
    repository = RunRepository(settings.runs_db_path)
    artifact_store = ArtifactStore(settings.artifacts_dir)
    runner = PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    return RuntimeWorker(
        repository=repository,
        runner=runner,
        poll_interval_seconds=settings.runtime_poll_interval_seconds,
    )
