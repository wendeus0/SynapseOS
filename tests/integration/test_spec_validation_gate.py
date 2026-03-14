from aignt_os.persistence import ArtifactStore, PersistedPipelineRunner, RunRepository
from aignt_os.specs import SpecValidationError
import pytest
from pathlib import Path


def test_run_fails_with_invalid_spec_and_generates_report(tmp_path):
    # Setup
    db_path = tmp_path / "runs.db"
    artifacts_path = tmp_path / "artifacts"
    repo = RunRepository(db_path)
    store = ArtifactStore(artifacts_path)

    runner = PersistedPipelineRunner(
        repository=repo,
        artifact_store=store,
        executors={},  # No executors needed as it should fail early
    )

    # Create invalid spec (missing ID)
    spec_path = tmp_path / "invalid_spec.md"
    spec_path.write_text("""---
type: feature
summary: Invalid spec
inputs: [none]
outputs: [none]
acceptance_criteria: [none]
non_goals: [none]
---

## Contexto
Invalid

## Objetivo
Invalid
""")

    # Create run
    run_id = runner.create_pending_run(spec_path=spec_path, stop_at="TEST_RED")

    try:
        runner.run_existing(run_id)
    except SpecValidationError:
        # Expected to raise, but we want to check side effects (persistence)
        pass
    except Exception as e:
        # It might be wrapped or different error depending on implementation
        # pipeline.py re-raises whatever exception
        # SpecValidator raises SpecValidationError
        if "SPEC" not in str(e):
            pytest.fail(f"Unexpected exception: {e}")

    # Verify status
    record = repo.get_run(run_id)
    assert record.status == "failed"
    # failure_message might be None if mark_run_failed wasn't called correctly or didn't save message?
    # Actually mark_run_failed updates status and failure_message.
    assert record.failure_message is not None
    assert "SPEC" in record.failure_message

    # Verify RUN_REPORT.md exists
    # Currently it likely DOES NOT exist
    report_path = artifacts_path / run_id / "RUN_REPORT.md"
    assert report_path.exists(), "RUN_REPORT.md should be generated even on validation failure"

    report_content = report_path.read_text()
    assert "SPEC" in report_content
