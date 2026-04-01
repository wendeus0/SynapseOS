from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

RETRYABLE_STATES = frozenset({"PLAN", "TEST_RED", "CODE_GREEN"})
TERMINAL_STATES = frozenset({"SECURITY", "SPEC_VALIDATION"})


class RetryableStepError(RuntimeError):
    """Marks a step failure as eligible for deterministic retry/reroute."""


class ReviewRejectedError(RuntimeError):
    """Signals that REVIEW requested rework and must return to CODE_GREEN."""


class AdapterOperationalError(RuntimeError):
    """Marks an adapter operational failure with a category."""

    def __init__(self, message: str, category: str) -> None:
        super().__init__(message)
        self.category = category


class RetryPolicy(BaseModel):
    model_config = ConfigDict(strict=True)

    max_retries: StrictInt = Field(default=2, ge=0)
    base_delay_seconds: float = Field(default=1.0, ge=0)
    max_delay_seconds: float = Field(default=60.0, ge=0)


class StepPolicy(BaseModel):
    model_config = ConfigDict(strict=True)

    step_name: StrictStr
    retry: RetryPolicy = Field(default_factory=RetryPolicy)


class SupervisorPolicies(BaseModel):
    model_config = ConfigDict(strict=True)

    default: RetryPolicy = Field(default_factory=RetryPolicy)
    step_overrides: dict[str, StepPolicy] = Field(default_factory=dict)

    def resolve_for_step(self, step_name: str) -> RetryPolicy:
        if step_name in self.step_overrides:
            return self.step_overrides[step_name].retry
        return self.default


def calculate_backoff(attempt: int, base_delay: float, max_delay: float) -> float:
    delay = base_delay * (2 ** (attempt - 1))
    return float(min(delay, max_delay))


class SupervisorDecision(BaseModel):
    model_config = ConfigDict(strict=True)

    action: StrictStr
    next_state: StrictStr
    route: StrictStr | None = None
    reason: StrictStr | None = None
    backoff_seconds: float | None = None


class Supervisor(BaseModel):
    model_config = ConfigDict(strict=True)

    max_retries: StrictInt = Field(default=2, ge=0)

    def decide_after_failure(
        self,
        *,
        state: str,
        error: Exception,
        attempt: int,
        available_routes: tuple[str, ...],
    ) -> SupervisorDecision:
        primary_route = available_routes[0] if available_routes else None
        fallback_route = available_routes[1] if len(available_routes) > 1 else None

        if state == "SPEC_VALIDATION":
            return SupervisorDecision(
                action="fail",
                next_state=state,
                reason="spec_validation_is_terminal",
            )

        if state == "SECURITY":
            return SupervisorDecision(
                action="fail",
                next_state=state,
                reason="security_is_terminal",
            )

        if isinstance(error, ReviewRejectedError) and state == "REVIEW":
            return self.decide_after_review_rejection()

        if isinstance(error, RetryableStepError) and state in RETRYABLE_STATES:
            if attempt <= self.max_retries:
                return SupervisorDecision(
                    action="retry",
                    next_state=state,
                    route=primary_route,
                    reason="retryable_failure_with_budget",
                )
            if fallback_route is not None:
                return SupervisorDecision(
                    action="reroute",
                    next_state=state,
                    route=fallback_route,
                    reason="retry_budget_exhausted_with_fallback",
                )

        return SupervisorDecision(
            action="fail",
            next_state=state,
            route=primary_route,
            reason="terminal_failure",
        )

    def decide_after_review_rejection(self) -> SupervisorDecision:
        return SupervisorDecision(
            action="return_to_code_green",
            next_state="CODE_GREEN",
            reason="review_requested_rework",
        )


class AdvancedSupervisor(BaseModel):
    model_config = ConfigDict(strict=True)

    policies: SupervisorPolicies = Field(default_factory=SupervisorPolicies)

    def _resolve_policy(self, state: str) -> RetryPolicy:
        return self.policies.resolve_for_step(state)

    def _is_terminal_state(self, state: str) -> bool:
        return state in TERMINAL_STATES

    def _is_short_circuit(self, error: Exception) -> bool:
        if isinstance(error, AdapterOperationalError):
            return error.category == "launcher_unavailable"
        return False

    def decide_after_failure(
        self,
        *,
        state: str,
        error: Exception,
        attempt: int,
        available_routes: tuple[str, ...],
    ) -> SupervisorDecision:
        primary_route = available_routes[0] if available_routes else None
        fallback_route = available_routes[1] if len(available_routes) > 1 else None

        if self._is_terminal_state(state):
            reason = f"{state.lower()}_is_terminal"
            return SupervisorDecision(
                action="fail",
                next_state=state,
                reason=reason,
            )

        if isinstance(error, ReviewRejectedError) and state == "REVIEW":
            return SupervisorDecision(
                action="return_to_code_green",
                next_state="CODE_GREEN",
                reason="review_requested_rework",
            )

        if self._is_short_circuit(error) and fallback_route is not None:
            return SupervisorDecision(
                action="reroute",
                next_state=state,
                route=fallback_route,
                reason="operational_error_short_circuit",
            )

        if (
            isinstance(error, (RetryableStepError, AdapterOperationalError))
            and state in RETRYABLE_STATES
        ):
            policy = self._resolve_policy(state)
            if attempt <= policy.max_retries:
                backoff = calculate_backoff(
                    attempt, policy.base_delay_seconds, policy.max_delay_seconds
                )
                return SupervisorDecision(
                    action="retry",
                    next_state=state,
                    route=primary_route,
                    reason="retryable_failure_with_budget",
                    backoff_seconds=backoff,
                )
            if fallback_route is not None:
                return SupervisorDecision(
                    action="reroute",
                    next_state=state,
                    route=fallback_route,
                    reason="retry_budget_exhausted_with_fallback",
                )

        return SupervisorDecision(
            action="fail",
            next_state=state,
            route=primary_route,
            reason="terminal_failure",
        )
