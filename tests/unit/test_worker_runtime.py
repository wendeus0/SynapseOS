from __future__ import annotations

from importlib import import_module
from pathlib import Path


def _write_valid_spec(path: Path, feature_id: str) -> None:
    path.write_text(
        f"""---
id: {feature_id}
type: feature
summary: Fixture spec for worker tests.
inputs:
  - raw_request
outputs:
  - validated_spec
acceptance_criteria:
  - must validate
non_goals: []
---

# Contexto

Fixture context.

# Objetivo

Fixture objective.
""",
        encoding="utf-8",
    )


def test_runtime_worker_processes_oldest_pending_run(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    worker_module = import_module("aignt_os.runtime.worker")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(repository=repository, runner=runner)

    first_spec = tmp_path / "FIRST.md"
    second_spec = tmp_path / "SECOND.md"
    _write_valid_spec(first_spec, "F08-first")
    _write_valid_spec(second_spec, "F08-second")

    first_run_id = repository.create_run(
        spec_path=first_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
    )
    second_run_id = repository.create_run(
        spec_path=second_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
    )

    processed_run_id = worker.poll_once()

    assert processed_run_id == first_run_id
    assert repository.get_run(first_run_id).status == "completed"
    assert repository.get_run(second_run_id).status == "pending"


def test_runtime_worker_ignores_locked_or_finalized_runs(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    worker_module = import_module("aignt_os.runtime.worker")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(repository=repository, runner=runner)

    locked_spec = tmp_path / "LOCKED.md"
    done_spec = tmp_path / "DONE.md"
    _write_valid_spec(locked_spec, "F08-locked")
    _write_valid_spec(done_spec, "F08-done")

    locked_run_id = repository.create_run(
        spec_path=locked_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
    )
    completed_run_id = repository.create_run(
        spec_path=done_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
    )
    assert repository.acquire_lock(locked_run_id) is True
    repository.mark_run_completed(completed_run_id, current_state="SPEC_VALIDATION")

    processed_run_id = worker.poll_once()

    assert processed_run_id is None
    assert repository.get_run(locked_run_id).status == "pending"
    assert repository.get_run(completed_run_id).status == "completed"
