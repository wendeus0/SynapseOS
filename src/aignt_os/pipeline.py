from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from aignt_os.config import AppSettings
from aignt_os.specs import (
    SpecDocument,
    validate_spec_file,
)
from aignt_os.specs import (
    SpecValidationError as _SpecValidationError,
)
from aignt_os.state_machine import LINEAR_STATE_FLOW, AIgntStateMachine
from aignt_os.supervisor import (
    RetryableStepError,
    Supervisor,
    SupervisorDecision,
)

PRIMARY_EXECUTOR_ROUTE = "primary"
PIPELINE_STOP_STATES = (
    "SPEC_VALIDATION",
    "PLAN",
    "TEST_RED",
    "CODE_GREEN",
    "QUALITY_GATE",
    "REVIEW",
    "SECURITY",
    "DOCUMENT",
)
PIPELINE_ENTRY_STATES = (
    "REQUEST",
    "SPEC_DISCOVERY",
    "SPEC_NORMALIZATION",
    "SPEC_VALIDATION",
    "PLAN",
    "TEST_RED",
    "CODE_GREEN",
    "QUALITY_GATE",
    "REVIEW",
    "SECURITY",
    "DOCUMENT",
    "COMPLETE",
)


class PipelineExecutionError(RuntimeError):
    pass


class PipelineCancelledError(PipelineExecutionError):
    pass


class PipelineStep(BaseModel):
    model_config = ConfigDict(strict=True)

    state: StrictStr
    description: StrictStr


class StepExecutionResult(BaseModel):
    model_config = ConfigDict(strict=True)

    artifacts: dict[str, StrictStr] = Field(default_factory=dict)
    raw_output: StrictStr | None = None
    clean_output: StrictStr | None = None
    tool_name: StrictStr | None = None
    return_code: int | None = None
    duration_ms: int | None = None
    timed_out: bool | None = None


class PipelineContext(BaseModel):
    model_config = ConfigDict(strict=True)

    spec_path: Path
    current_state: StrictStr
    run_id: StrictStr | None = None
    step_history: list[StrictStr] = Field(default_factory=list)
    artifacts: dict[str, StrictStr] = Field(default_factory=dict)
    supervisor_decisions: list[StrictStr] = Field(default_factory=list)
    validated_spec: SpecDocument | None = None


class StepExecutor(Protocol):
    def execute(
        self,
        step: PipelineStep,
        context: PipelineContext,
    ) -> StepExecutionResult: ...


class CancellationChecker(Protocol):
    def check_cancellation(self, context: PipelineContext) -> bool: ...


class PipelineObserver(Protocol):
    def on_run_started(self, context: PipelineContext) -> None: ...

    def on_step_completed(
        self,
        step: PipelineStep,
        context: PipelineContext,
        result: StepExecutionResult | None,
    ) -> None: ...

    def on_run_completed(self, context: PipelineContext) -> None: ...

    def on_run_failed(
        self,
        context: PipelineContext,
        step: PipelineStep | None,
        error: Exception,
    ) -> None: ...

    def on_supervisor_decision(
        self,
        step: PipelineStep,
        context: PipelineContext,
        decision: SupervisorDecision,
        error: Exception,
    ) -> None: ...


PIPELINE_STEPS: dict[str, PipelineStep] = {
    "SPEC_VALIDATION": PipelineStep(
        state="SPEC_VALIDATION",
        description="Validate the feature SPEC before planning.",
    ),
    "PLAN": PipelineStep(
        state="PLAN",
        description="Produce the planning hand-off for the current feature.",
    ),
    "TEST_RED": PipelineStep(
        state="TEST_RED",
        description="Produce the failing test hand-off for the current feature.",
    ),
    "CODE_GREEN": PipelineStep(
        state="CODE_GREEN",
        description="Produce the minimal implementation to satisfy the failing tests.",
    ),
    "QUALITY_GATE": PipelineStep(
        state="QUALITY_GATE",
        description="Validate tests, lint, typecheck and regression before security review.",
    ),
    "REVIEW": PipelineStep(
        state="REVIEW",
        description="Review the current delta and request rework when needed.",
    ),
    "SECURITY": PipelineStep(
        state="SECURITY",
        description="Review security-sensitive aspects before reporting completion.",
    ),
    "DOCUMENT": PipelineStep(
        state="DOCUMENT",
        description="Generate the final RUN_REPORT.md for the current run.",
    ),
}

SpecValidationError = _SpecValidationError


class PipelineEngine:
    def __init__(
        self,
        *,
        settings: AppSettings | None = None,
        executors: dict[str, StepExecutor | dict[str, StepExecutor]] | None = None,
        state_machine: AIgntStateMachine | None = None,
        observer: PipelineObserver | None = None,
        supervisor: Supervisor | None = None,
        cancellation_checker: CancellationChecker | None = None,
    ) -> None:
        self.settings = settings or AppSettings()
        self.executors = self._normalize_executors(executors or {})
        self.state_machine = state_machine or AIgntStateMachine()
        self.observer = observer
        self.cancellation_checker = cancellation_checker

        if supervisor is None:
            # Create default supervisor using settings
            self.supervisor = Supervisor(max_retries=self.settings.max_retries)
        else:
            self.supervisor = supervisor

    def run(
        self,
        spec_path: Path,
        *,
        stop_at: str = "TEST_RED",
        run_id: str | None = None,
    ) -> PipelineContext:
        if stop_at not in PIPELINE_STOP_STATES:
            raise ValueError(f"Unsupported stop_at state: {stop_at}.")

        self._validate_entry_state()
        context = PipelineContext(
            spec_path=spec_path,
            current_state=self.state_machine.current_state,
            run_id=run_id,
        )
        current_step: PipelineStep | None = None

        if self.observer is not None:
            self.observer.on_run_started(context)

        try:
            while True:
                if (
                    self.cancellation_checker
                    and self.cancellation_checker.check_cancellation(context)
                ):
                    raise PipelineCancelledError("Pipeline execution was cancelled.")

                current_state = self.state_machine.current_state

                if current_state in {"REQUEST", "SPEC_DISCOVERY", "SPEC_NORMALIZATION"}:
                    self.state_machine.advance_to(self._next_state(current_state))
                    context.current_state = self.state_machine.current_state
                    continue

                if current_state == "COMPLETE":
                    context.current_state = current_state
                    if self.observer is not None:
                        self.observer.on_run_completed(context)
                    return context

                if current_state == "SPEC_VALIDATION":
                    current_step = PIPELINE_STEPS[current_state]
                    self._execute_spec_validation(context)
                    if self.observer is not None:
                        self.observer.on_step_completed(current_step, context, None)
                    if stop_at == "SPEC_VALIDATION":
                        if self.observer is not None:
                            self.observer.on_run_completed(context)
                        return context
                    self.state_machine.advance_to("PLAN")
                    context.current_state = self.state_machine.current_state
                    continue

                if current_state in {
                    "PLAN",
                    "TEST_RED",
                    "CODE_GREEN",
                    "QUALITY_GATE",
                    "REVIEW",
                    "SECURITY",
                    "DOCUMENT",
                }:
                    current_step = PIPELINE_STEPS[current_state]
                    result = self._run_runtime_step(current_step, context)
                    if result is None:
                        continue
                    context.artifacts.update(result.artifacts)
                    context.step_history.append(current_step.state)
                    context.current_state = current_state
                    if self.observer is not None:
                        self.observer.on_step_completed(current_step, context, result)
                    if stop_at == current_state:
                        if self.observer is not None:
                            self.observer.on_run_completed(context)
                        return context
                    self.state_machine.advance_to(self._next_state(current_state))
                    context.current_state = self.state_machine.current_state
                    continue

                raise PipelineExecutionError(
                    f"Current state '{current_state}' is outside the supported F09 pipeline range."
                )
        except Exception as exc:
            if self.observer is not None:
                self.observer.on_run_failed(context, current_step, exc)
            raise

    def _execute_spec_validation(self, context: PipelineContext) -> None:
        spec_document = validate_spec_file(context.spec_path)
        context.validated_spec = spec_document
        context.artifacts["spec_id"] = spec_document.metadata.id
        context.artifacts["spec_summary"] = spec_document.metadata.summary
        context.step_history.append("SPEC_VALIDATION")
        context.current_state = "SPEC_VALIDATION"

    def _execute_runtime_step(
        self,
        step: PipelineStep,
        context: PipelineContext,
        *,
        route: str = PRIMARY_EXECUTOR_ROUTE,
    ) -> StepExecutionResult:
        executor = self.executors.get(step.state, {}).get(route)
        if executor is None:
            raise PipelineExecutionError(
                f"Missing executor for pipeline step '{step.state}' on route '{route}'."
            )

        # We use a ThreadPoolExecutor to enforce timeout on synchronous executors
        from concurrent.futures import ThreadPoolExecutor, TimeoutError

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(executor.execute, step, context)
            try:
                return future.result(timeout=self.settings.execution_timeout_seconds)
            except TimeoutError as exc:
                raise RetryableStepError(
                    f"Step '{step.state}' exceeded timeout of "
                    f"{self.settings.execution_timeout_seconds}s."
                ) from exc

    def _run_runtime_step(
        self,
        step: PipelineStep,
        context: PipelineContext,
    ) -> StepExecutionResult | None:
        attempt = 0
        route = PRIMARY_EXECUTOR_ROUTE

        while True:
            try:
                return self._execute_runtime_step(step, context, route=route)
            except Exception as exc:
                attempt += 1
                decision = self._decide_after_failure(
                    step=step,
                    context=context,
                    error=exc,
                    attempt=attempt,
                )

                if decision.action == "retry":
                    route = decision.route or route
                    continue

                if decision.action == "reroute":
                    route = decision.route or route
                    continue

                if decision.action == "return_to_code_green":
                    context.step_history.append(step.state)
                    context.current_state = step.state
                    self.state_machine.advance_to("CODE_GREEN")
                    context.current_state = self.state_machine.current_state
                    return None

                raise exc

    def _validate_entry_state(self) -> None:
        if self.state_machine.current_state not in PIPELINE_ENTRY_STATES:
            raise PipelineExecutionError(
                f"Current state '{self.state_machine.current_state}' is not supported by F10."
            )

    def _next_state(self, current_state: str) -> str:
        try:
            current_index = LINEAR_STATE_FLOW.index(current_state)
        except ValueError as exc:
            raise PipelineExecutionError(
                f"Current state '{current_state}' is not part of the linear state flow."
            ) from exc

        next_index = current_index + 1
        if next_index >= len(LINEAR_STATE_FLOW):
            raise PipelineExecutionError(
                f"Current state '{current_state}' has no next state in the linear flow."
            )
        return LINEAR_STATE_FLOW[next_index]

    def _normalize_executors(
        self,
        executors: dict[str, StepExecutor | dict[str, StepExecutor]],
    ) -> dict[str, dict[str, StepExecutor]]:
        normalized: dict[str, dict[str, StepExecutor]] = {}
        for state, executor_config in executors.items():
            if isinstance(executor_config, dict):
                normalized[state] = dict(executor_config)
            else:
                normalized[state] = {PRIMARY_EXECUTOR_ROUTE: executor_config}
        return normalized

    def _decide_after_failure(
        self,
        *,
        step: PipelineStep,
        context: PipelineContext,
        error: Exception,
        attempt: int,
    ) -> SupervisorDecision:
        if self.supervisor is None:
            raise error

        decision = self.supervisor.decide_after_failure(
            state=step.state,
            error=error,
            attempt=attempt,
            available_routes=tuple(self.executors.get(step.state, {}).keys()),
        )
        context.supervisor_decisions.append(f"{decision.action}:{step.state}")

        observer_callback = (
            None
            if self.observer is None
            else getattr(
                self.observer,
                "on_supervisor_decision",
                None,
            )
        )
        if observer_callback is not None:
            observer_callback(step, context, decision, error)

        return decision
