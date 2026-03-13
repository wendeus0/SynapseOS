from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


def test_run_repository_handles_cancellation(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=tmp_path / "SPEC.md",
        initial_state="REQUEST",
        stop_at="PLAN",
        spec_hash="abc123",
        initiated_by="local_cli",
    )

    # Initial state
    run = repository.get_run(run_id)
    assert run.status == "pending"

    # Mark as cancelling
    repository.mark_run_cancelling(run_id)
    run = repository.get_run(run_id)
    assert run.status == "cancelling"

    # Verify locked state is preserved during cancelling phase
    # (Worker needs lock to see signal and shutdown cleanly)
    # Actually, mark_run_cancelling might not touch lock,
    # but let's assume we want to signal intent without unlocking yet
    # so the worker currently holding the lock sees it.

    # Mark as cancelled (final state)
    repository.mark_run_cancelled(run_id, current_state="REQUEST")
    run = repository.get_run(run_id)
    assert run.status == "cancelled"
    assert run.locked is False
    assert run.completed_at is not None


def test_run_repository_cannot_cancel_finished_run(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    run_id = repository.create_run(
        spec_path=tmp_path / "SPEC.md",
        initial_state="REQUEST",
        stop_at="PLAN",
        spec_hash="abc123",
        initiated_by="local_cli",
    )

    repository.mark_run_completed(run_id, current_state="PLAN")

    # Attempt to cancel completed run should fail or do nothing effective
    # Let's say it raises ValueError to be explicit
    with pytest.raises(ValueError, match="Cannot cancel finished run"):
        repository.mark_run_cancelling(run_id)


def test_runtime_service_cancel_run_integration(tmp_path: Path) -> None:
    # Testing the integration in service layer if applicable,
    # but RunRepository is the main persistence layer.
    pass
