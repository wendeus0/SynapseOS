from __future__ import annotations

from importlib import import_module
from pathlib import Path


def test_run_report_generator_matches_expected_fixture(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    reporting = import_module("synapse_os.reporting")

    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("# fixture\n", encoding="utf-8")

    run_id = repository.create_run(
        spec_path=spec_path,
        initial_state="REQUEST",
        stop_at="DOCUMENT",
        spec_hash="abc123",
        initiated_by="local_cli",
    )
    repository.acquire_lock(run_id)
    repository.mark_run_running(run_id, current_state="SPEC_VALIDATION")
    artifact_store.save_named_artifact(
        run_id=run_id,
        step_state="SPEC_VALIDATION",
        artifact_name="spec_id",
        content="F06-pipeline-engine-linear",
    )
    artifact_store.save_named_artifact(
        run_id=run_id,
        step_state="SPEC_VALIDATION",
        artifact_name="spec_summary",
        content="Implementar a primeira engine linear do Synapse-Flow",
    )
    repository.record_step(run_id, state="SPEC_VALIDATION", status="completed")
    repository.record_step(
        run_id,
        state="PLAN",
        status="completed",
        tool_name="fake-executor",
        return_code=0,
        duration_ms=45,
        timed_out=False,
    )
    artifact_store.save_named_artifact(
        run_id=run_id,
        step_state="PLAN",
        artifact_name="plan_md",
        content="# Plan\n",
    )
    repository.record_step(run_id, state="DOCUMENT", status="completed")
    repository.record_event(
        run_id,
        state="REQUEST",
        event_type="security_provenance_recorded",
        message="Provenance recorded for initiated_by=local_cli spec_hash=abc123.",
    )
    repository.record_event(
        run_id,
        state="REQUEST",
        event_type="run_context_initialized",
        message=(f"Run context initialized for initiated_by=local_cli workspace={tmp_path}."),
    )
    repository.record_event(
        run_id,
        state="REQUEST",
        event_type="run_started",
        message=f"Run started at REQUEST. workspace={tmp_path}",
    )
    repository.record_event(
        run_id,
        state="REQUEST",
        event_type="state_transitioned",
        message="REQUEST -> SPEC_VALIDATION",
    )
    repository.record_event(
        run_id,
        state="SPEC_VALIDATION",
        event_type="step_started",
        message="Step SPEC_VALIDATION started.",
    )
    repository.record_event(
        run_id,
        state="SPEC_VALIDATION",
        event_type="step_completed",
        message="Step SPEC_VALIDATION completed.",
    )
    repository.record_event(
        run_id,
        state="SPEC_VALIDATION",
        event_type="state_transitioned",
        message="SPEC_VALIDATION -> PLAN",
    )
    repository.record_event(
        run_id,
        state="PLAN",
        event_type="step_started",
        message="Step PLAN started.",
    )
    repository.record_event(
        run_id,
        state="PLAN",
        event_type="step_completed",
        message="Step PLAN completed.",
    )
    repository.record_event(
        run_id,
        state="DOCUMENT",
        event_type="run_completed",
        message="Run completed at DOCUMENT.",
    )
    repository.mark_run_completed(run_id, current_state="DOCUMENT")

    generator = reporting.RunReportGenerator(repository=repository, artifact_store=artifact_store)
    report_content = generator.build(run_id)

    expected_report = (
        Path(__file__).resolve().parents[1] / "fixtures" / "reports" / "expected_run_report.md"
    ).read_text(encoding="utf-8")

    assert report_content == expected_report.format(run_id=run_id, workspace_path=tmp_path)
