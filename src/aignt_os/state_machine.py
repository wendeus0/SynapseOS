from __future__ import annotations

from dataclasses import dataclass, field


class InvalidStateTransition(ValueError):
    pass


LINEAR_STATE_FLOW: tuple[str, ...] = (
    "REQUEST",
    "SPEC_DISCOVERY",
    "SPEC_NORMALIZATION",
    "SPEC_VALIDATION",
    "PLAN",
    "TEST_RED",
    "CODE_GREEN",
    "REVIEW",
    "SECURITY",
    "DOCUMENT",
    "COMPLETE",
)

TERMINAL_STATES = {"COMPLETE", "FAILED"}


@dataclass
class AIgntStateMachine:
    current_state: str = "REQUEST"
    _allowed_transitions: dict[str, set[str]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._allowed_transitions = _build_allowed_transitions()

    def advance_to(self, next_state: str) -> None:
        allowed_states = self._allowed_transitions.get(self.current_state, set())
        if next_state not in allowed_states:
            raise InvalidStateTransition(
                f"Cannot transition from {self.current_state} to {next_state}."
            )

        self.current_state = next_state

    def fail(self) -> None:
        self.advance_to("FAILED")


def _build_allowed_transitions() -> dict[str, set[str]]:
    transitions: dict[str, set[str]] = {}

    for current_state, next_state in zip(LINEAR_STATE_FLOW, LINEAR_STATE_FLOW[1:], strict=False):
        transitions[current_state] = {next_state, "FAILED"}

    transitions["REVIEW"].add("CODE_GREEN")
    transitions["COMPLETE"] = set()
    transitions["FAILED"] = set()
    return transitions
