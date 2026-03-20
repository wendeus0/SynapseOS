from __future__ import annotations

import hashlib
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
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

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
        workspace_root=tmp_path,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="sync")

    run_record = repository.get_run(result.run_id)
    assert result.status == "completed"
    assert result.dispatch_mode_resolved == "sync"
    assert run_record.status == "completed"
    assert run_record.current_state == "SPEC_VALIDATION"
    assert run_record.initiated_by == "local_cli"
    assert run_record.spec_hash == hashlib.sha256(spec_path.read_bytes()).hexdigest()


def test_run_dispatch_service_uses_workspace_provider_to_resolve_spec_path(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")
    runtime_contracts = import_module("synapse_os.runtime_contracts")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    spec_path = workspace_root / "SPEC.md"
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
        workspace_root=workspace_root,
        workspace_provider=runtime_contracts.LocalWorkspaceProvider(workspace_root),
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="sync")

    run_record = repository.get_run(result.run_id)
    assert run_record.spec_path == str(spec_path.resolve())


def test_run_dispatch_service_preserves_default_workspace_when_run_isolation_is_not_enabled(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

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
        workspace_root=tmp_path,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="sync")

    run_record = repository.get_run(result.run_id)
    assert run_record.workspace_path == str(tmp_path)


def test_run_dispatch_service_auto_queues_when_runtime_is_ready(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

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
        workspace_root=tmp_path,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="auto")

    run_record = repository.get_run(result.run_id)
    assert result.status == "queued"
    assert result.dispatch_mode_resolved == "async"
    assert run_record.status == "pending"
    assert run_record.current_state == "REQUEST"
    assert run_record.locked is False
    assert run_record.initiated_by == "local_cli"
    assert run_record.spec_hash == hashlib.sha256(spec_path.read_bytes()).hexdigest()


def test_run_dispatch_service_explicit_async_queues_pending_run(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

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
        workspace_root=tmp_path,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="async")

    run_record = repository.get_run(result.run_id)
    assert result.status == "queued"
    assert result.dispatch_mode_resolved == "async"
    assert run_record.status == "pending"
    assert run_record.current_state == "REQUEST"
    assert run_record.initiated_by == "local_cli"
    assert run_record.spec_hash == hashlib.sha256(spec_path.read_bytes()).hexdigest()


def test_run_dispatch_service_requires_running_runtime_for_authenticated_async(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")
    runtime_state_module = import_module("synapse_os.runtime.state")

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
        workspace_root=tmp_path,
        initiated_by="operator-user",
        runtime_state_provider=lambda: runtime_state_module.RuntimeState(status="stopped"),
        enforce_async_runtime_ownership=True,
    )

    with pytest.raises(
        dispatch_module.AsyncDispatchRuntimeUnavailableError,
        match="running resident runtime",
    ):
        service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="async")

    assert repository.list_runs() == []


def test_run_dispatch_service_rejects_authenticated_async_for_other_runtime_owner(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")
    runtime_state_module = import_module("synapse_os.runtime.state")

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
        workspace_root=tmp_path,
        initiated_by="operator-b",
        runtime_state_provider=lambda: runtime_state_module.RuntimeState(
            status="running",
            pid=1234,
            process_identity="fixture-runtime",
            started_by="operator-a",
        ),
        enforce_async_runtime_ownership=True,
    )

    with pytest.raises(
        dispatch_module.AsyncDispatchOwnershipError,
        match="another principal",
    ):
        service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="auto")

    assert repository.list_runs() == []


def test_run_dispatch_service_allows_authenticated_async_for_legacy_runtime_binding(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")
    runtime_state_module = import_module("synapse_os.runtime.state")

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
        workspace_root=tmp_path,
        initiated_by="operator-user",
        runtime_state_provider=lambda: runtime_state_module.RuntimeState(
            status="running",
            pid=1234,
            process_identity="fixture-runtime",
            started_by=None,
        ),
        enforce_async_runtime_ownership=True,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="async")

    run_record = repository.get_run(result.run_id)
    assert result.status == "queued"
    assert result.dispatch_mode_resolved == "async"
    assert run_record.status == "pending"
    assert run_record.initiated_by == "operator-user"


def test_run_dispatch_service_rejects_missing_spec_path(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

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
        workspace_root=tmp_path,
    )

    with pytest.raises(FileNotFoundError, match="SPEC file not found"):
        service.dispatch(tmp_path / "missing.md", stop_at="SPEC_VALIDATION", mode="sync")

    assert repository.list_runs() == []


def test_run_dispatch_service_rejects_invalid_spec_before_persisting_run(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")
    specs_module = import_module("synapse_os.specs")

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
        workspace_root=tmp_path,
    )

    with pytest.raises(specs_module.SpecValidationError, match="SPEC"):
        service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="async")

    assert repository.list_runs() == []


def test_run_dispatch_service_rejects_invalid_mode(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

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
        workspace_root=tmp_path,
    )

    with pytest.raises(ValueError, match="Unsupported dispatch mode"):
        service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="invalid")  # type: ignore[arg-type]


def test_run_dispatch_service_rejects_spec_outside_workspace_root(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside_spec = tmp_path / "outside" / "SPEC.md"
    outside_spec.parent.mkdir()
    _write_valid_spec(outside_spec)
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
        workspace_root=workspace_root,
    )

    with pytest.raises(FileNotFoundError, match="SPEC file not found"):
        service.dispatch(outside_spec, stop_at="SPEC_VALIDATION", mode="sync")

    assert repository.list_runs() == []


def test_run_dispatch_service_rejects_directory_outside_workspace_root(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
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
        workspace_root=workspace_root,
    )

    with pytest.raises(FileNotFoundError, match="SPEC file not found"):
        service.dispatch(outside_dir, stop_at="SPEC_VALIDATION", mode="sync")

    assert repository.list_runs() == []


def test_run_dispatch_service_persists_canonical_spec_path_for_valid_run(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    dispatch_module = import_module("synapse_os.runtime.dispatch")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    spec_path = workspace_root / "SPEC.md"
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
        workspace_root=workspace_root,
    )

    result = service.dispatch(spec_path, stop_at="SPEC_VALIDATION", mode="sync")

    assert repository.get_run(result.run_id).spec_path == str(spec_path.resolve())
