from unittest.mock import MagicMock

import pytest

from aignt_os.pipeline import PipelineCancelledError, PipelineContext, PipelineEngine


class MockCancellationChecker:
    def __init__(self):
        self.call_count = 0
        
    def check_cancellation(self, context: PipelineContext) -> bool:
        self.call_count += 1
        # Cancel on the 2nd check (simulating cancellation signal)
        return self.call_count >= 2

def test_pipeline_engine_stops_when_cancellation_checker_returns_true():
    # Setup
    mock_executor = MagicMock()
    mock_executor.execute.return_value = MagicMock(
        artifacts={}, raw_output="", clean_output=""
    )
    
    checker = MockCancellationChecker()

    engine = PipelineEngine(
        executors={
            "PLAN": mock_executor,
            "TEST_RED": mock_executor,
        },
        cancellation_checker=checker
    )
    
    # Init state machine at PLAN to simulate a running pipeline
    engine.state_machine.current_state = "PLAN"
    
    # Execution
    with pytest.raises(PipelineCancelledError):
        # Pass a real Path because Pydantic validates it
        from pathlib import Path
        engine.run(spec_path=Path("/tmp/spec.md"), stop_at="CODE_GREEN")
    
    # Verification
    # 1. First loop: state=PLAN. checker called (1). Returns False. Executes PLAN.
    # 2. Advance to TEST_RED.
    # 3. Second loop: state=TEST_RED. checker called (2). Returns True. Raises.
    
    # So PLAN should have executed ONCE.
    assert mock_executor.execute.call_count == 1
    # Check it was called with PLAN step
    assert mock_executor.execute.call_args[0][0].state == "PLAN"
