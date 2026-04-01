from __future__ import annotations

from importlib import import_module

import pytest


def _supervisor_module():
    return import_module("synapse_os.supervisor")


class TestRetryPolicyModel:
    def test_retry_policy_has_expected_fields(self) -> None:
        supervisor = _supervisor_module()
        policy = supervisor.RetryPolicy(
            max_retries=3, base_delay_seconds=1.0, max_delay_seconds=60.0
        )
        assert policy.max_retries == 3
        assert policy.base_delay_seconds == 1.0
        assert policy.max_delay_seconds == 60.0

    def test_retry_policy_default_values(self) -> None:
        supervisor = _supervisor_module()
        policy = supervisor.RetryPolicy()
        assert policy.max_retries == 2
        assert policy.base_delay_seconds == 1.0
        assert policy.max_delay_seconds == 60.0


class TestStepPolicyModel:
    def test_step_policy_holds_retry_policy(self) -> None:
        supervisor = _supervisor_module()
        step_policy = supervisor.StepPolicy(
            step_name="TEST_RED",
            retry=supervisor.RetryPolicy(max_retries=5),
        )
        assert step_policy.step_name == "TEST_RED"
        assert step_policy.retry.max_retries == 5


class TestSupervisorPoliciesModel:
    def test_supervisor_policies_holds_default_and_overrides(self) -> None:
        supervisor = _supervisor_module()
        default_policy = supervisor.RetryPolicy(max_retries=2)
        test_red_policy = supervisor.StepPolicy(
            step_name="TEST_RED",
            retry=supervisor.RetryPolicy(max_retries=5),
        )
        policies = supervisor.SupervisorPolicies(
            default=default_policy,
            step_overrides={"TEST_RED": test_red_policy},
        )
        assert policies.default.max_retries == 2
        assert policies.step_overrides["TEST_RED"].retry.max_retries == 5

    def test_supervisor_policies_resolves_step_specific_policy(self) -> None:
        supervisor = _supervisor_module()
        policies = supervisor.SupervisorPolicies()
        resolved = policies.resolve_for_step("TEST_RED")
        assert resolved.max_retries == 2

        policies.step_overrides["TEST_RED"] = supervisor.StepPolicy(
            step_name="TEST_RED",
            retry=supervisor.RetryPolicy(max_retries=5),
        )
        resolved = policies.resolve_for_step("TEST_RED")
        assert resolved.max_retries == 5


class TestCalculateBackoff:
    def test_backoff_doubles_each_attempt(self) -> None:
        supervisor = _supervisor_module()
        delay = supervisor.calculate_backoff(attempt=1, base_delay=1.0, max_delay=60.0)
        assert delay == 1.0
        delay = supervisor.calculate_backoff(attempt=2, base_delay=1.0, max_delay=60.0)
        assert delay == 2.0
        delay = supervisor.calculate_backoff(attempt=3, base_delay=1.0, max_delay=60.0)
        assert delay == 4.0
        delay = supervisor.calculate_backoff(attempt=4, base_delay=1.0, max_delay=60.0)
        assert delay == 8.0

    def test_backoff_respects_max_cap(self) -> None:
        supervisor = _supervisor_module()
        delay = supervisor.calculate_backoff(attempt=10, base_delay=1.0, max_delay=60.0)
        assert delay == 60.0

    def test_backoff_with_different_base(self) -> None:
        supervisor = _supervisor_module()
        delay = supervisor.calculate_backoff(attempt=1, base_delay=2.0, max_delay=60.0)
        assert delay == 2.0
        delay = supervisor.calculate_backoff(attempt=2, base_delay=2.0, max_delay=60.0)
        assert delay == 4.0


class TestAdvancedSupervisorPerStepRetries:
    def test_test_red_respects_own_max_retries(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor(
            policies=supervisor_mod.SupervisorPolicies(
                default=supervisor_mod.RetryPolicy(max_retries=2),
                step_overrides={
                    "TEST_RED": supervisor_mod.StepPolicy(
                        step_name="TEST_RED",
                        retry=supervisor_mod.RetryPolicy(max_retries=5),
                    ),
                },
            ),
        )
        decision = advanced.decide_after_failure(
            state="TEST_RED",
            error=supervisor_mod.RetryableStepError("failure"),
            attempt=4,
            available_routes=("primary",),
        )
        assert decision.action == "retry"

    def test_plan_respects_own_max_retries(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor(
            policies=supervisor_mod.SupervisorPolicies(
                default=supervisor_mod.RetryPolicy(max_retries=2),
                step_overrides={
                    "PLAN": supervisor_mod.StepPolicy(
                        step_name="PLAN",
                        retry=supervisor_mod.RetryPolicy(max_retries=1),
                    ),
                },
            ),
        )
        decision = advanced.decide_after_failure(
            state="PLAN",
            error=supervisor_mod.RetryableStepError("failure"),
            attempt=2,
            available_routes=("primary",),
        )
        assert decision.action == "fail"
        assert decision.reason == "terminal_failure"


class TestAdvancedSupervisorTerminalSteps:
    def test_security_remains_terminal(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor()
        decision = advanced.decide_after_failure(
            state="SECURITY",
            error=ValueError("insecure"),
            attempt=1,
            available_routes=("primary",),
        )
        assert decision.action == "fail"
        assert decision.reason == "security_is_terminal"

    def test_spec_validation_remains_terminal(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor()
        decision = advanced.decide_after_failure(
            state="SPEC_VALIDATION",
            error=ValueError("bad spec"),
            attempt=1,
            available_routes=("primary",),
        )
        assert decision.action == "fail"
        assert decision.reason == "spec_validation_is_terminal"


class TestAdvancedSupervisorFallbackRouting:
    def test_reroutes_to_fallback_after_exhausting_primary_retries(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor(
            policies=supervisor_mod.SupervisorPolicies(
                default=supervisor_mod.RetryPolicy(max_retries=2),
            ),
        )
        decision = advanced.decide_after_failure(
            state="CODE_GREEN",
            error=supervisor_mod.RetryableStepError("failure"),
            attempt=3,
            available_routes=("primary", "fallback"),
        )
        assert decision.action == "reroute"
        assert decision.route == "fallback"
        assert decision.reason == "retry_budget_exhausted_with_fallback"


class TestAdvancedSupervisorBackoffDelay:
    def test_returns_backoff_delay_in_decision(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor(
            policies=supervisor_mod.SupervisorPolicies(
                default=supervisor_mod.RetryPolicy(
                    max_retries=3, base_delay_seconds=1.0, max_delay_seconds=60.0
                ),
            ),
        )
        decision = advanced.decide_after_failure(
            state="CODE_GREEN",
            error=supervisor_mod.RetryableStepError("failure"),
            attempt=2,
            available_routes=("primary",),
        )
        assert decision.action == "retry"
        assert decision.backoff_seconds == 2.0

    def test_backoff_caps_at_max_delay(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor(
            policies=supervisor_mod.SupervisorPolicies(
                default=supervisor_mod.RetryPolicy(
                    max_retries=10, base_delay_seconds=10.0, max_delay_seconds=60.0
                ),
            ),
        )
        decision = advanced.decide_after_failure(
            state="CODE_GREEN",
            error=supervisor_mod.RetryableStepError("failure"),
            attempt=10,
            available_routes=("primary",),
        )
        assert decision.action == "retry"
        assert decision.backoff_seconds == 60.0


class TestAdvancedSupervisorOperationalError:
    def test_launcher_unavailable_short_circuits(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor()
        op_error = supervisor_mod.AdapterOperationalError(
            "launcher unavailable",
            category="launcher_unavailable",
        )
        decision = advanced.decide_after_failure(
            state="CODE_GREEN",
            error=op_error,
            attempt=1,
            available_routes=("primary", "fallback"),
        )
        assert decision.action == "reroute"
        assert decision.route == "fallback"
        assert decision.reason == "operational_error_short_circuit"

    def test_other_operational_errors_still_retry(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor(
            policies=supervisor_mod.SupervisorPolicies(
                default=supervisor_mod.RetryPolicy(max_retries=2),
            ),
        )
        op_error = supervisor_mod.AdapterOperationalError(
            "some error",
            category="timeout",
        )
        decision = advanced.decide_after_failure(
            state="CODE_GREEN",
            error=op_error,
            attempt=1,
            available_routes=("primary",),
        )
        assert decision.action == "retry"


class TestAdvancedSupervisorDefaults:
    def test_advanced_supervisor_inherits_supervisor_interface(self) -> None:
        supervisor_mod = _supervisor_module()
        advanced = supervisor_mod.AdvancedSupervisor()
        decision = advanced.decide_after_failure(
            state="CODE_GREEN",
            error=supervisor_mod.RetryableStepError("failure"),
            attempt=1,
            available_routes=("primary",),
        )
        assert decision.action == "retry"
        assert decision.next_state == "CODE_GREEN"
