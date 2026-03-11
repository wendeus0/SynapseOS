from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from aignt_os.specs import SpecDocument, validate_spec_file
from aignt_os.state_machine import LINEAR_STATE_FLOW, AIgntStateMachine

PIPELINE_STOP_STATES = ("PLAN", "TEST_RED")
PIPELINE_ENTRY_STATES = (
    "REQUEST",
    "SPEC_DISCOVERY",
    "SPEC_NORMALIZATION",
    "SPEC_VALIDATION",
    "PLAN",
    "TEST_RED",
)


class PipelineExecutionError(RuntimeError):
    pass


class PipelineStep(BaseModel):
    model_config = ConfigDict(strict=True)

    state: StrictStr
    description: StrictStr


class StepExecutionResult(BaseModel):
    model_config = ConfigDict(strict=True)

    artifacts: dict[str, StrictStr] = Field(default_factory=dict)


class PipelineContext(BaseModel):
    model_config = ConfigDict(strict=True)

    spec_path: Path
    current_state: StrictStr
    step_history: list[StrictStr] = Field(default_factory=list)
    artifacts: dict[str, StrictStr] = Field(default_factory=dict)
    validated_spec: SpecDocument | None = None


class StepExecutor(Protocol):
    def execute(
        self,
        step: PipelineStep,
        context: PipelineContext,
    ) -> StepExecutionResult: ...


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
}


class PipelineEngine:
    def __init__(
        self,
        *,
        executors: dict[str, StepExecutor] | None = None,
        state_machine: AIgntStateMachine | None = None,
    ) -> None:
        self.executors = dict(executors or {})
        self.state_machine = state_machine or AIgntStateMachine()

    def run(self, spec_path: Path, *, stop_at: str = "TEST_RED") -> PipelineContext:
        if stop_at not in PIPELINE_STOP_STATES:
            raise ValueError(f"Unsupported stop_at state: {stop_at}.")

        self._validate_entry_state()
        context = PipelineContext(
            spec_path=spec_path,
            current_state=self.state_machine.current_state,
        )

        while True:
            current_state = self.state_machine.current_state

            if current_state in {"REQUEST", "SPEC_DISCOVERY", "SPEC_NORMALIZATION"}:
                self.state_machine.advance_to(self._next_state(current_state))
                context.current_state = self.state_machine.current_state
                continue

            if current_state == "SPEC_VALIDATION":
                self._execute_spec_validation(context)
                if stop_at == "SPEC_VALIDATION":
                    return context
                self.state_machine.advance_to("PLAN")
                context.current_state = self.state_machine.current_state
                continue

            if current_state in {"PLAN", "TEST_RED"}:
                step = PIPELINE_STEPS[current_state]
                result = self._execute_runtime_step(step, context)
                context.artifacts.update(result.artifacts)
                context.step_history.append(step.state)
                context.current_state = current_state
                if stop_at == current_state:
                    return context
                self.state_machine.advance_to(self._next_state(current_state))
                context.current_state = self.state_machine.current_state
                continue

            raise PipelineExecutionError(
                f"Current state '{current_state}' is outside the supported F06 pipeline range."
            )

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
    ) -> StepExecutionResult:
        executor = self.executors.get(step.state)
        if executor is None:
            raise PipelineExecutionError(f"Missing executor for pipeline step '{step.state}'.")
        return executor.execute(step, context)

    def _validate_entry_state(self) -> None:
        if self.state_machine.current_state not in PIPELINE_ENTRY_STATES:
            raise PipelineExecutionError(
                f"Current state '{self.state_machine.current_state}' is not supported by F06."
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
