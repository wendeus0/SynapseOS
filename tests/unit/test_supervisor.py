from __future__ import annotations

from importlib import import_module


def _supervisor_module():
    return import_module("aignt_os.supervisor")


def test_supervisor_requests_retry_after_recoverable_step_failure() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="CODE_GREEN",
        error=supervisor.RetryableStepError("temporary failure"),
        attempt=1,
        available_routes=("primary",),
    )

    assert decision.action == "retry"
    assert decision.next_state == "CODE_GREEN"
    assert decision.route == "primary"


def test_supervisor_reroutes_after_repeated_step_failures() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="TEST_RED",
        error=supervisor.RetryableStepError("tool failure"),
        attempt=3,
        available_routes=("primary", "fallback"),
    )

    assert decision.action == "reroute"
    assert decision.next_state == "TEST_RED"
    assert decision.route == "fallback"


def test_supervisor_marks_terminal_failure_after_spec_validation_error() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="SPEC_VALIDATION",
        error=ValueError("invalid spec"),
        attempt=1,
        available_routes=("primary",),
    )

    assert decision.action == "fail"
    assert decision.next_state == "SPEC_VALIDATION"


def test_supervisor_returns_to_code_green_after_review_rejection() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_review_rejection()

    assert decision.action == "return_to_code_green"
    assert decision.next_state == "CODE_GREEN"
