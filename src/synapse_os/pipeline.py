from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from synapse_os.config import AppSettings
from synapse_os.hooks import HookDispatcher, HookRejectedError
from synapse_os.runtime_contracts import (
    HookContext,
    RunContext,
    RunLifecycleHooks,
    WorkspaceContext,
    WorkspaceProvider,
)
from synapse_os.specs import (
    SpecDocument,
    validate_spec_file,
)
from synapse_os.specs import (
    SpecValidationError as _SpecValidationError,
)
from synapse_os.state_machine import (
    LINEAR_STATE_FLOW,
    PipelineState,
    SynapseStateMachine,
)
from synapse_os.supervisor import (
    RetryableStepError,
    Supervisor,
    SupervisorDecision,
)

PRIMARY_EXECUTOR_ROUTE = "primary"
PIPELINE_STOP_STATES = (
    PipelineState.SPEC_VALIDATION,
    PipelineState.PLAN,
    PipelineState.TEST_RED,
    PipelineState.CODE_GREEN,
    PipelineState.QUALITY_GATE,
    PipelineState.REVIEW,
    PipelineState.SECURITY,
    PipelineState.DOCUMENT,
)
PIPELINE_ENTRY_STATES = (
    PipelineState.REQUEST,
    PipelineState.SPEC_DISCOVERY,
    PipelineState.SPEC_NORMALIZATION,
    PipelineState.SPEC_VALIDATION,
    PipelineState.PLAN,
    PipelineState.TEST_RED,
    PipelineState.CODE_GREEN,
    PipelineState.QUALITY_GATE,
    PipelineState.REVIEW,
    PipelineState.SECURITY,
    PipelineState.DOCUMENT,
    PipelineState.COMPLETE,
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
    run_context: RunContext
    run_id: StrictStr | None = None
    step_history: list[StrictStr] = Field(default_factory=list)
    artifacts: dict[StrictStr, StrictStr] = Field(default_factory=dict)
    supervisor_decisions: list[StrictStr] = Field(default_factory=list)
    validated_spec: SpecDocument | None = None
    hooks_active: list[StrictStr] = Field(default_factory=list)


class StepExecutor(Protocol):
    def execute(
        self,
        step: PipelineStep,
        context: PipelineContext,
    ) -> StepExecutionResult: ...


class CancellationChecker(Protocol):
    def check_cancellation(self, context: PipelineContext) -> bool: ...


PipelineObserver = RunLifecycleHooks


PIPELINE_STEPS: dict[str, PipelineStep] = {
    PipelineState.SPEC_VALIDATION: PipelineStep(
        state=PipelineState.SPEC_VALIDATION,
        description="Validate the feature SPEC before planning.",
    ),
    PipelineState.PLAN: PipelineStep(
        state=PipelineState.PLAN,
        description="Produce the planning hand-off for the current feature.",
    ),
    PipelineState.TEST_RED: PipelineStep(
        state=PipelineState.TEST_RED,
        description="Produce the failing test hand-off for the current feature.",
    ),
    PipelineState.CODE_GREEN: PipelineStep(
        state=PipelineState.CODE_GREEN,
        description="Produce the minimal implementation to satisfy the failing tests.",
    ),
    PipelineState.QUALITY_GATE: PipelineStep(
        state=PipelineState.QUALITY_GATE,
        description="Validate tests, lint, typecheck and regression before security review.",
    ),
    PipelineState.REVIEW: PipelineStep(
        state=PipelineState.REVIEW,
        description="Review the current delta and request rework when needed.",
    ),
    PipelineState.SECURITY: PipelineStep(
        state=PipelineState.SECURITY,
        description="Review security-sensitive aspects before reporting completion.",
    ),
    PipelineState.DOCUMENT: PipelineStep(
        state=PipelineState.DOCUMENT,
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
        state_machine: SynapseStateMachine | None = None,
        observer: PipelineObserver | None = None,
        supervisor: Supervisor | None = None,
        cancellation_checker: CancellationChecker | None = None,
        workspace_provider: WorkspaceProvider | None = None,
        hook_dispatcher: HookDispatcher | None = None,
    ) -> None:
        self.settings = settings or AppSettings()
        self.executors = self._normalize_executors(executors or {})
        self.state_machine = state_machine or SynapseStateMachine()
        self.observer = observer
        self.cancellation_checker = cancellation_checker
        self.workspace_provider = workspace_provider
        self.hook_dispatcher = hook_dispatcher

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
        initiated_by: str = "system",
    ) -> PipelineContext:
        if stop_at not in PIPELINE_STOP_STATES:
            raise ValueError(f"Unsupported stop_at state: {stop_at}.")

        self._validate_entry_state()
        workspace = self._resolve_workspace(spec_path)
        context = PipelineContext(
            spec_path=workspace.spec_path,
            current_state=self.state_machine.current_state,
            run_context=RunContext(
                run_id=run_id,
                initiated_by=initiated_by,
                workspace=workspace,
            ),
            run_id=run_id,
        )
        current_step: PipelineStep | None = None
        pending_entry_transition = (
            self.state_machine.current_state
            if self.state_machine.current_state
            in {
                PipelineState.REQUEST,
                PipelineState.SPEC_DISCOVERY,
                PipelineState.SPEC_NORMALIZATION,
            }
            else None
        )

        self._notify_optional("on_run_context_initialized", context)

        if self.hook_dispatcher is None and self.settings.hooks:
            self.hook_dispatcher = HookDispatcher(global_hooks=self.settings.hooks)

        if self.hook_dispatcher is not None:
            context.hooks_active = list(self.hook_dispatcher.hooks_active)

        if self.observer is not None:
            self.observer.on_run_started(context)

        try:
            while True:
                if self.cancellation_checker and self.cancellation_checker.check_cancellation(
                    context
                ):
                    raise PipelineCancelledError("Pipeline execution was cancelled.")

                current_state = self.state_machine.current_state

                if current_state in {
                    PipelineState.REQUEST,
                    PipelineState.SPEC_DISCOVERY,
                    PipelineState.SPEC_NORMALIZATION,
                }:
                    next_state = self._next_state(current_state)
                    self.state_machine.advance_to(next_state)
                    context.current_state = self.state_machine.current_state
                    if (
                        context.current_state == PipelineState.SPEC_VALIDATION
                        and pending_entry_transition is not None
                    ):
                        self._notify_optional(
                            "on_state_transition",
                            pending_entry_transition,
                            PipelineState.SPEC_VALIDATION,
                            context,
                        )
                        pending_entry_transition = None
                    continue

                if current_state == PipelineState.COMPLETE:
                    context.current_state = current_state
                    if self.observer is not None:
                        self.observer.on_run_completed(context)
                    return context

                if current_state == PipelineState.SPEC_VALIDATION:
                    current_step = PIPELINE_STEPS[current_state]
                    self._notify_optional("on_step_started", current_step, context)
                    self._run_step_with_hooks(current_step, context)
                    if stop_at == PipelineState.SPEC_VALIDATION:
                        if self.observer is not None:
                            self.observer.on_run_completed(context)
                        return context
                    next_state = self._next_state(current_state)
                    self._advance_with_hooks(current_state, next_state, context)
                    continue

                if current_state in {
                    PipelineState.PLAN,
                    PipelineState.TEST_RED,
                    PipelineState.CODE_GREEN,
                    PipelineState.QUALITY_GATE,
                    PipelineState.REVIEW,
                    PipelineState.SECURITY,
                    PipelineState.DOCUMENT,
                }:
                    current_step = PIPELINE_STEPS[current_state]
                    self._notify_optional("on_step_started", current_step, context)
                    advanced = self._run_step_with_hooks(current_step, context)
                    if not advanced:
                        continue
                    if stop_at == current_state:
                        if self.observer is not None:
                            self.observer.on_run_completed(context)
                        return context
                    next_state = self._next_state(current_state)
                    self._advance_with_hooks(current_state, next_state, context)
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
        context.step_history.append(PipelineState.SPEC_VALIDATION)
        context.current_state = PipelineState.SPEC_VALIDATION

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
                    self.state_machine.advance_to(PipelineState.CODE_GREEN)
                    context.current_state = self.state_machine.current_state
                    return None

                raise exc

    def _validate_entry_state(self) -> None:
        if self.state_machine.current_state not in PIPELINE_ENTRY_STATES:
            raise PipelineExecutionError(
                f"Current state '{self.state_machine.current_state}' is not supported by F10."
            )

    def _resolve_workspace(self, spec_path: Path) -> WorkspaceContext:
        if self.workspace_provider is not None:
            return self.workspace_provider.resolve(spec_path)

        resolved_spec_path = spec_path.resolve()
        return WorkspaceContext(
            root_path=resolved_spec_path.parent,
            spec_path=resolved_spec_path,
        )

    def _notify_optional(self, method_name: str, *args: object) -> None:
        if self.observer is None:
            return
        callback = getattr(self.observer, method_name, None)
        if callback is None:
            return
        callback(*args)

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

    def _run_step_with_hooks(
        self,
        step: PipelineStep,
        context: PipelineContext,
    ) -> bool:
        if self.hook_dispatcher is not None:
            hook_ctx = HookContext(
                run_id=context.run_id or "unknown",
                step_name=step.state,
                current_state=context.current_state,
            )
            try:
                self.hook_dispatcher.dispatch_pre("pre_step", hook_ctx)
            except HookRejectedError as exc:
                context.step_history.append(step.state)
                context.current_state = step.state
                raise RetryableStepError(f"Hook rejected step '{step.state}'") from exc

        if step.state == PipelineState.SPEC_VALIDATION:
            self._execute_spec_validation(context)
            if self.observer is not None:
                self.observer.on_step_completed(step, context, None)
        else:
            result = self._run_runtime_step(step, context)
            if result is None:
                return False

            context.artifacts.update(result.artifacts)
            context.step_history.append(step.state)
            context.current_state = step.state
            if self.observer is not None:
                self.observer.on_step_completed(step, context, result)

        if self.hook_dispatcher is not None:
            hook_ctx = HookContext(
                run_id=context.run_id or "unknown",
                step_name=step.state,
                current_state=context.current_state,
            )
            self.hook_dispatcher.dispatch_post("post_step", hook_ctx)

        return True

    def _advance_with_hooks(
        self,
        from_state: str,
        to_state: str,
        context: PipelineContext,
    ) -> None:
        if self.hook_dispatcher is not None:
            hook_ctx = HookContext(
                run_id=context.run_id or "unknown",
                current_state=from_state,
            )
            self.hook_dispatcher.dispatch_pre("pre_state_transition", hook_ctx)

        self._notify_optional("on_state_transition", from_state, to_state, context)
        self.state_machine.advance_to(to_state)
        context.current_state = self.state_machine.current_state

        if self.hook_dispatcher is not None:
            hook_ctx = HookContext(
                run_id=context.run_id or "unknown",
                current_state=to_state,
            )
            self.hook_dispatcher.dispatch_post("post_state_transition", hook_ctx)
