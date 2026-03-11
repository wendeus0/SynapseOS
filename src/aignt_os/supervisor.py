from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

RETRYABLE_STATES = frozenset({"PLAN", "TEST_RED", "CODE_GREEN"})


class RetryableStepError(RuntimeError):
    """Marks a step failure as eligible for deterministic retry/reroute."""


class ReviewRejectedError(RuntimeError):
    """Signals that REVIEW requested rework and must return to CODE_GREEN."""


class SupervisorDecision(BaseModel):
    model_config = ConfigDict(strict=True)

    action: StrictStr
    next_state: StrictStr
    route: StrictStr | None = None
    reason: StrictStr | None = None


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
