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
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")

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
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")

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


def test_runtime_worker_fails_pending_run_when_spec_hash_changes(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(repository=repository, runner=runner)

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path, "F26-mismatch")
    run_id = runner.create_pending_run(spec_path, stop_at="SPEC_VALIDATION")
    spec_path.write_text(spec_path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

    processed_run_id = worker.poll_once()
    run_record = repository.get_run(run_id)
    events = repository.list_events(run_id)

    assert processed_run_id == run_id
    assert run_record.status == "failed"
    assert run_record.current_state == "REQUEST"
    assert [event.event_type for event in events] == [
        "security_provenance_recorded",
        "security_spec_hash_mismatch",
        "run_failed",
    ]


def test_runtime_worker_skips_incompatible_owner_and_processes_next_compatible(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")
    runtime_state_module = import_module("synapse_os.runtime.state")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(
        repository=repository,
        runner=runner,
        runtime_state_provider=lambda: runtime_state_module.RuntimeState(
            status="running",
            pid=1234,
            process_identity="fixture-runtime",
            started_by="operator-a",
        ),
    )

    first_spec = tmp_path / "FIRST.md"
    second_spec = tmp_path / "SECOND.md"
    _write_valid_spec(first_spec, "F35-first")
    _write_valid_spec(second_spec, "F35-second")

    incompatible_run_id = repository.create_run(
        spec_path=first_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-b",
    )
    compatible_run_id = repository.create_run(
        spec_path=second_spec,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-a",
    )

    processed_run_id = worker.poll_once()

    assert processed_run_id == compatible_run_id
    assert repository.get_run(compatible_run_id).status == "completed"
    incompatible_run = repository.get_run(incompatible_run_id)
    assert incompatible_run.status == "pending"
    assert incompatible_run.locked is False
    incompatible_events = repository.list_events(incompatible_run_id)
    assert [event.event_type for event in incompatible_events] == ["runtime_owner_skip"]
    assert "runtime_started_by=operator-a" in incompatible_events[0].message
    assert "run_initiated_by=operator-b" in incompatible_events[0].message


def test_runtime_worker_accepts_legacy_run_for_authenticated_runtime(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")
    runtime_state_module = import_module("synapse_os.runtime.state")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(
        repository=repository,
        runner=runner,
        runtime_state_provider=lambda: runtime_state_module.RuntimeState(
            status="running",
            pid=1234,
            process_identity="fixture-runtime",
            started_by="operator-a",
        ),
    )

    spec_path = tmp_path / "LEGACY.md"
    _write_valid_spec(spec_path, "F35-legacy")
    legacy_run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="local_cli",
    )

    processed_run_id = worker.poll_once()

    assert processed_run_id == legacy_run_id
    assert repository.get_run(legacy_run_id).status == "completed"
    assert "runtime_owner_skip" not in [
        event.event_type for event in repository.list_events(legacy_run_id)
    ]


def test_runtime_worker_deduplicates_same_owner_skip_message(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")
    runtime_state_module = import_module("synapse_os.runtime.state")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(
        repository=repository,
        runner=runner,
        runtime_state_provider=lambda: runtime_state_module.RuntimeState(
            status="running",
            pid=1234,
            process_identity="fixture-runtime",
            started_by="operator-a",
        ),
    )

    spec_path = tmp_path / "ONLY-INCOMPATIBLE.md"
    _write_valid_spec(spec_path, "F36-incompatible")
    incompatible_run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
        initiated_by="operator-b",
    )

    first_processed = worker.poll_once()
    second_processed = worker.poll_once()

    incompatible_events = repository.list_events(incompatible_run_id)
    assert first_processed is None
    assert second_processed is None
    assert [event.event_type for event in incompatible_events] == ["runtime_owner_skip"]


def test_runtime_worker_sleeps_when_idle(tmp_path: Path) -> None:
    from unittest.mock import patch

    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(
        repository=repository,
        runner=runner,
        poll_interval_seconds=0.05,
    )

    with patch("synapse_os.runtime.worker.time.sleep") as mock_sleep:
        worker.sleep_when_idle()

    mock_sleep.assert_called_once_with(0.05)


def test_build_runtime_worker_constructs_with_correct_poll_interval(
    tmp_path: Path,
) -> None:
    from synapse_os.config import AppSettings

    settings = AppSettings()
    settings.workspace_root = tmp_path
    settings.runtime_state_dir = tmp_path / "runtime"
    settings.runs_db_path = tmp_path / "runs.sqlite3"
    settings.artifacts_dir = tmp_path / "artifacts"
    settings.runtime_poll_interval_seconds = 1.5

    worker = import_module("synapse_os.runtime.worker").build_runtime_worker(settings)

    assert worker.poll_interval_seconds == 1.5
    assert worker.repository is not None
    assert worker.runner is not None


def test_runtime_owner_returns_none_when_provider_is_none(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(
        repository=repository,
        runner=runner,
        runtime_state_provider=None,
    )

    owner = worker._runtime_owner()

    assert owner is None


def test_runtime_worker_handles_runner_exception_gracefully(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    worker_module = import_module("synapse_os.runtime.worker")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    worker = worker_module.RuntimeWorker(repository=repository, runner=runner)

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path, "F56-error-handling")
    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="SPEC_VALIDATION",
    )

    processed_run_id = worker.poll_once()

    assert processed_run_id == run_id
    run_record = repository.get_run(run_id)
    assert run_record.status in ("completed", "failed")
