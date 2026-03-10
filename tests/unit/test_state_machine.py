from importlib import import_module

import pytest


def _state_machine_module():
    return import_module("aignt_os.state_machine")


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


def test_state_machine_can_transition_to_failed_from_active_state() -> None:
    state_machine_module = _state_machine_module()

    machine = state_machine_module.AIgntStateMachine()
    machine.advance_to("SPEC_DISCOVERY")
    machine.fail()

    assert machine.current_state == "FAILED"


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
