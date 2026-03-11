from importlib import import_module

import pytest


def _state_machine_module():
    return import_module("aignt_os.state_machine")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_state_machine_follows_minimal_happy_path_to_complete() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()

    assert machine.current_state == "REQUEST"

    machine.advance_to("SPEC_DISCOVERY")
    machine.advance_to("SPEC_NORMALIZATION")
    machine.advance_to("SPEC_VALIDATION")
    machine.advance_to("PLAN")
    machine.advance_to("TEST_RED")
    machine.advance_to("CODE_GREEN")
    machine.advance_to("REVIEW")
    machine.advance_to("SECURITY")
    machine.advance_to("DOCUMENT")
    machine.advance_to("COMPLETE")

    assert machine.current_state == "COMPLETE"


def test_state_machine_starts_at_request() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()

    assert machine.current_state == "REQUEST"


# ---------------------------------------------------------------------------
# Ordered transitions — individual blocking tests
# ---------------------------------------------------------------------------


def test_state_machine_blocks_plan_before_spec_validation() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    machine.advance_to("SPEC_DISCOVERY")
    machine.advance_to("SPEC_NORMALIZATION")

    with pytest.raises(state_machine_module.InvalidStateTransition, match="PLAN"):
        machine.advance_to("PLAN")


def test_state_machine_rejects_invalid_transition_that_skips_flow_order() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()

    with pytest.raises(state_machine_module.InvalidStateTransition, match="TEST_RED"):
        machine.advance_to("TEST_RED")


def test_state_machine_allows_review_to_return_to_code_green() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    for state in (
        "SPEC_DISCOVERY",
        "SPEC_NORMALIZATION",
        "SPEC_VALIDATION",
        "PLAN",
        "TEST_RED",
        "CODE_GREEN",
        "REVIEW",
    ):
        machine.advance_to(state)

    machine.advance_to("CODE_GREEN")

    assert machine.current_state == "CODE_GREEN"


# ---------------------------------------------------------------------------
# Parametrised invalid skip transitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "advance_before, skip_to",
    [
        # From REQUEST, trying to jump forward
        ([], "SPEC_NORMALIZATION"),
        ([], "SPEC_VALIDATION"),
        ([], "PLAN"),
        ([], "TEST_RED"),
        ([], "CODE_GREEN"),
        ([], "COMPLETE"),
        # From SPEC_DISCOVERY, trying to skip SPEC_NORMALIZATION
        (["SPEC_DISCOVERY"], "SPEC_VALIDATION"),
        (["SPEC_DISCOVERY"], "PLAN"),
        # From SPEC_NORMALIZATION, trying to skip SPEC_VALIDATION
        (["SPEC_DISCOVERY", "SPEC_NORMALIZATION"], "PLAN"),
        # From SPEC_VALIDATION, trying to skip PLAN
        (
            ["SPEC_DISCOVERY", "SPEC_NORMALIZATION", "SPEC_VALIDATION"],
            "TEST_RED",
        ),
        # Going backwards
        (["SPEC_DISCOVERY"], "REQUEST"),
        (
            ["SPEC_DISCOVERY", "SPEC_NORMALIZATION", "SPEC_VALIDATION"],
            "SPEC_DISCOVERY",
        ),
    ],
    ids=[
        "REQUEST→SPEC_NORMALIZATION",
        "REQUEST→SPEC_VALIDATION",
        "REQUEST→PLAN",
        "REQUEST→TEST_RED",
        "REQUEST→CODE_GREEN",
        "REQUEST→COMPLETE",
        "SPEC_DISCOVERY→SPEC_VALIDATION",
        "SPEC_DISCOVERY→PLAN",
        "SPEC_NORMALIZATION→PLAN",
        "SPEC_VALIDATION→TEST_RED",
        "SPEC_DISCOVERY→REQUEST(backward)",
        "SPEC_VALIDATION→SPEC_DISCOVERY(backward)",
    ],
)
def test_state_machine_rejects_out_of_order_transition(
    advance_before: list[str], skip_to: str
) -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    for state in advance_before:
        machine.advance_to(state)

    with pytest.raises(state_machine_module.InvalidStateTransition):
        machine.advance_to(skip_to)


# ---------------------------------------------------------------------------
# FAILED from every active state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "advance_before",
    [
        [],
        ["SPEC_DISCOVERY"],
        ["SPEC_DISCOVERY", "SPEC_NORMALIZATION"],
        ["SPEC_DISCOVERY", "SPEC_NORMALIZATION", "SPEC_VALIDATION"],
        ["SPEC_DISCOVERY", "SPEC_NORMALIZATION", "SPEC_VALIDATION", "PLAN"],
        [
            "SPEC_DISCOVERY",
            "SPEC_NORMALIZATION",
            "SPEC_VALIDATION",
            "PLAN",
            "TEST_RED",
        ],
    ],
    ids=[
        "from_REQUEST",
        "from_SPEC_DISCOVERY",
        "from_SPEC_NORMALIZATION",
        "from_SPEC_VALIDATION",
        "from_PLAN",
        "from_TEST_RED",
    ],
)
def test_state_machine_can_transition_to_failed_from_active_state(
    advance_before: list[str],
) -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    for state in advance_before:
        machine.advance_to(state)

    machine.fail()

    assert machine.current_state == "FAILED"


# ---------------------------------------------------------------------------
# Terminal states
# ---------------------------------------------------------------------------


def test_state_machine_rejects_transition_after_terminal_complete() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()

    for state in (
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
    ):
        machine.advance_to(state)

    with pytest.raises(state_machine_module.InvalidStateTransition, match="COMPLETE"):
        machine.advance_to("FAILED")


def test_state_machine_rejects_any_transition_after_terminal_failed() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    machine.fail()

    assert machine.current_state == "FAILED"

    with pytest.raises(state_machine_module.InvalidStateTransition):
        machine.advance_to("SPEC_DISCOVERY")


@pytest.mark.parametrize(
    "next_state",
    [
        "REQUEST",
        "SPEC_DISCOVERY",
        "PLAN",
        "TEST_RED",
        "COMPLETE",
        "FAILED",
    ],
)
def test_state_machine_rejects_all_transitions_after_complete(next_state: str) -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    for state in (
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
    ):
        machine.advance_to(state)

    with pytest.raises(state_machine_module.InvalidStateTransition):
        machine.advance_to(next_state)
