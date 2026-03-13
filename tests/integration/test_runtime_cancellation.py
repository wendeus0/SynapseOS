from dataclasses import replace
from unittest.mock import MagicMock

from aignt_os.persistence import ArtifactStore, PersistedPipelineRunner, RunRepository
from aignt_os.pipeline import PipelineCancelledError


def test_runtime_stops_on_cancellation(tmp_path):
    # Setup
    db_path = tmp_path / "runs.db"
    artifacts_path = tmp_path / "artifacts"
    repo = RunRepository(db_path)
    store = ArtifactStore(artifacts_path)
    
    # We need executors. We can use mocks for steps.
    mock_executor = MagicMock()
    mock_executor.execute.return_value = MagicMock(
        artifacts={}, raw_output="ok", clean_output="ok"
    )
    
    # Create run
    spec_path = tmp_path / "spec.md"
    spec_path.write_text("""---
id: F40-test
type: feature
summary: Test spec
inputs: [none]
outputs: [none]
acceptance_criteria: [none]
non_goals: [none]
---

## Contexto
Test

## Objetivo
Test
""")
    
    runner = PersistedPipelineRunner(
        repository=repo,
        artifact_store=store,
        executors={
            "PLAN": mock_executor,
            "TEST_RED": mock_executor,
        }
    )
    
    run_id = runner.create_pending_run(spec_path=spec_path, stop_at="TEST_RED")
    
    # Mock repository.get_run to simulate cancellation
    # We need to preserve the real behavior for initial calls
    real_get_run = repo.get_run
    
    call_count = 0
    def side_effect(rid):
        nonlocal call_count
        call_count += 1
        record = real_get_run(rid)
        
        # Simulating cancellation after SPEC_VALIDATION (which happens early)
        # The engine checks cancellation before EACH step.
        # Loop:
        # 1. REQUEST -> ... -> SPEC_VALIDATION.
        # 2. Check cancellation.
        # 3. PLAN.
        # 4. Check cancellation.
        # 5. TEST_RED.
        
        # If we cancel at 4th call (approx), it should stop before TEST_RED.
        if call_count >= 3: 
            return replace(record, status="cancelling")
        return record

    repo.get_run = MagicMock(side_effect=side_effect)
    
    # Execution
    try:
        runner.run_existing(run_id)
    except PipelineCancelledError:
        pass # Expected
    
    # Verification
    # Restore get_run to verify real DB state
    repo.get_run = real_get_run
    final_record = repo.get_run(run_id)
    assert final_record.status == "cancelled"
    
    # Verify events
    events = repo.list_events(run_id)
    assert any(e.event_type == "run_cancelled" for e in events)
