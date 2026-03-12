from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F08-fixture
type: feature
summary: Fixture spec for runtime dispatch tests.
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


def test_run_dispatch_service_executes_inline_when_mode_is_sync(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=lambda: False,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="sync")

    run_record = repository.get_run(result.run_id)
    assert result.status == "completed"
    assert result.dispatch_mode_resolved == "sync"
    assert run_record.status == "completed"
    assert run_record.current_state == "SPEC_VALIDATION"


def test_run_dispatch_service_auto_queues_when_runtime_is_ready(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=lambda: True,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="auto")

    run_record = repository.get_run(result.run_id)
    assert result.status == "queued"
    assert result.dispatch_mode_resolved == "async"
    assert run_record.status == "pending"
    assert run_record.current_state == "REQUEST"
    assert run_record.locked is False


def test_run_dispatch_service_explicit_async_queues_pending_run(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=lambda: False,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="async")

    run_record = repository.get_run(result.run_id)
    assert result.status == "queued"
    assert result.dispatch_mode_resolved == "async"
    assert run_record.status == "pending"
    assert run_record.current_state == "REQUEST"


def test_run_dispatch_service_rejects_missing_spec_path(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=lambda: False,
    )

    with pytest.raises(FileNotFoundError, match="SPEC file not found"):
        service.dispatch(tmp_path / "missing.md", stop_at="SPEC_VALIDATION", mode="sync")

    assert repository.list_runs() == []


def test_run_dispatch_service_rejects_invalid_spec_before_persisting_run(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")
    specs_module = import_module("aignt_os.specs")

    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# Contexto\n\nSem front matter.\n", encoding="utf-8")
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=lambda: True,
    )

    with pytest.raises(specs_module.SpecValidationError, match="SPEC"):
        service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="async")

    assert repository.list_runs() == []


def test_run_dispatch_service_rejects_invalid_mode(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    dispatch_module = import_module("aignt_os.runtime.dispatch")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
    )
    service = dispatch_module.RunDispatchService(
        repository=repository,
        runner=runner,
        is_runtime_ready=lambda: False,
    )

    with pytest.raises(ValueError, match="Unsupported dispatch mode"):
        service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="invalid")  # type: ignore[arg-type]
