from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class InvalidStateTransition(ValueError):
    pass


class PipelineState(StrEnum):
    REQUEST = "REQUEST"
    SPEC_DISCOVERY = "SPEC_DISCOVERY"
    SPEC_NORMALIZATION = "SPEC_NORMALIZATION"
    SPEC_VALIDATION = "SPEC_VALIDATION"
    PLAN = "PLAN"
    TEST_RED = "TEST_RED"
    CODE_GREEN = "CODE_GREEN"
    QUALITY_GATE = "QUALITY_GATE"
    REVIEW = "REVIEW"
    SECURITY = "SECURITY"
    DOCUMENT = "DOCUMENT"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


LINEAR_STATE_FLOW: tuple[PipelineState, ...] = (
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

TERMINAL_STATES: frozenset[PipelineState] = frozenset({
    PipelineState.COMPLETE,
    PipelineState.FAILED,
    PipelineState.CANCELLED,
})


@dataclass
class SynapseStateMachine:
    current_state: PipelineState | str = PipelineState.REQUEST
    _allowed_transitions: dict[PipelineState, set[PipelineState]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if isinstance(self.current_state, str):
            self.current_state = PipelineState(self.current_state)
        self._allowed_transitions = _build_allowed_transitions()

    def advance_to(self, next_state: PipelineState | str) -> None:
        target = PipelineState(next_state)
        # Ensure current_state is treated as PipelineState for dict lookup
        current = PipelineState(self.current_state)
        allowed_states = self._allowed_transitions.get(current, set())
        
        if target not in allowed_states:
            raise InvalidStateTransition(
                f"Cannot transition from {current} to {target}."
            )

        self.current_state = target

    def fail(self) -> None:
        self.advance_to(PipelineState.FAILED)
        
    def cancel(self) -> None:
        self.advance_to(PipelineState.CANCELLED)


def _build_allowed_transitions() -> dict[PipelineState, set[PipelineState]]:
    transitions: dict[PipelineState, set[PipelineState]] = {}

    for current_state, next_state in zip(LINEAR_STATE_FLOW, LINEAR_STATE_FLOW[1:], strict=False):
        transitions[current_state] = {next_state, PipelineState.FAILED, PipelineState.CANCELLED}

    # Add specific loops
    if PipelineState.REVIEW in transitions:
        transitions[PipelineState.REVIEW].add(PipelineState.CODE_GREEN)

    # Terminal states have no transitions
    for state in TERMINAL_STATES:
        transitions[state] = set()

    return transitions
