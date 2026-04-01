from __future__ import annotations

from importlib import import_module


def _supervisor_module():
    return import_module("synapse_os.supervisor")


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


def test_supervisor_marks_terminal_failure_after_security_error() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="SECURITY",
        error=ValueError("insecure pattern"),
        attempt=1,
        available_routes=("primary",),
    )

    assert decision.action == "fail"
    assert decision.next_state == "SECURITY"
    assert decision.reason == "security_is_terminal"


def test_supervisor_terminal_failure_when_no_fallback_route() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="PLAN",
        error=supervisor.RetryableStepError("failure"),
        attempt=3,
        available_routes=("primary",),
    )

    assert decision.action == "fail"
    assert decision.next_state == "PLAN"
    assert decision.reason == "terminal_failure"


def test_supervisor_retry_budget_exhausted_at_max_retries() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="CODE_GREEN",
        error=supervisor.RetryableStepError("failure"),
        attempt=2,
        available_routes=("primary", "fallback"),
    )

    assert decision.action == "retry"
    assert decision.reason == "retryable_failure_with_budget"


def test_supervisor_reroute_when_budget_exceeded_with_fallback() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="TEST_RED",
        error=supervisor.RetryableStepError("failure"),
        attempt=3,
        available_routes=("primary", "fallback"),
    )

    assert decision.action == "reroute"
    assert decision.route == "fallback"
    assert decision.reason == "retry_budget_exhausted_with_fallback"


def test_supervisor_ignores_retryable_error_in_non_retryable_state() -> None:
    supervisor = _supervisor_module()

    decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="REVIEW",
        error=supervisor.RetryableStepError("failure"),
        attempt=1,
        available_routes=("primary",),
    )

    assert decision.action == "fail"
    assert decision.reason == "terminal_failure"


def test_supervisor_decision_contains_correct_reason() -> None:
    supervisor = _supervisor_module()

    retry_decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="PLAN",
        error=supervisor.RetryableStepError("failure"),
        attempt=1,
        available_routes=("primary",),
    )
    assert retry_decision.reason == "retryable_failure_with_budget"

    terminal_decision = supervisor.Supervisor(max_retries=2).decide_after_failure(
        state="SPEC_VALIDATION",
        error=ValueError("bad"),
        attempt=1,
        available_routes=("primary",),
    )
    assert terminal_decision.reason == "spec_validation_is_terminal"

    review_decision = supervisor.Supervisor(max_retries=2).decide_after_review_rejection()
    assert review_decision.reason == "review_requested_rework"
