"""Pipeline rework and review state tests.

Tests cover the state machine's support for REVIEW and backward transition
patterns in the AIgnt-Synapse-Flow, validating that:
- REVIEW is a valid state in the linear flow
- transitions from CODE_GREEN to REVIEW are valid
- REVIEW can transition to SECURITY (forward path)
- REVIEW and CODE_GREEN can transition to FAILED (rework terminal path)
- the state machine enforces that rework cannot skip states forward

These tests document the intended rework behavior using the state machine
directly, preparing the ground for a future Supervisor implementation.
"""

from __future__ import annotations

import pytest

from aignt_os.state_machine import AIgntStateMachine, InvalidStateTransition


def _make_sm_at(state: str) -> AIgntStateMachine:
    """Create a fresh state machine positioned at the given state by advancing through the flow."""
    sm = AIgntStateMachine()
    flow = [
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
    ]
    for target in flow:
        if sm.current_state == state:
            break
        sm.advance_to(target)
    return sm


def test_review_rework_code_green_transitions_to_review() -> None:
    sm = _make_sm_at("CODE_GREEN")
    sm.advance_to("REVIEW")
    assert sm.current_state == "REVIEW"


def test_review_rework_review_transitions_to_security_on_approval() -> None:
    sm = _make_sm_at("REVIEW")
    sm.advance_to("SECURITY")
    assert sm.current_state == "SECURITY"


def test_review_rework_review_can_return_to_code_green_for_rework() -> None:
    sm = _make_sm_at("REVIEW")
    sm.advance_to("CODE_GREEN")
    assert sm.current_state == "CODE_GREEN"


def test_review_rework_review_can_transition_to_failed() -> None:
    sm = _make_sm_at("REVIEW")
    sm.advance_to("FAILED")
    assert sm.current_state == "FAILED"


def test_review_rework_code_green_can_transition_to_failed() -> None:
    sm = _make_sm_at("CODE_GREEN")
    sm.advance_to("FAILED")
    assert sm.current_state == "FAILED"


def test_review_rework_state_machine_does_not_allow_review_to_skip_to_complete() -> None:
    sm = _make_sm_at("REVIEW")
    with pytest.raises(InvalidStateTransition):
        sm.advance_to("COMPLETE")


def test_review_rework_state_machine_does_not_allow_review_to_go_back_to_plan() -> None:
    sm = _make_sm_at("REVIEW")
    with pytest.raises(InvalidStateTransition):
        sm.advance_to("PLAN")


def test_review_rework_state_machine_does_not_allow_code_green_to_jump_to_document() -> None:
    sm = _make_sm_at("CODE_GREEN")
    with pytest.raises(InvalidStateTransition):
        sm.advance_to("DOCUMENT")


def test_review_rework_failed_is_terminal_no_further_transitions() -> None:
    sm = _make_sm_at("CODE_GREEN")
    sm.advance_to("FAILED")
    with pytest.raises(InvalidStateTransition):
        sm.advance_to("CODE_GREEN")


def test_review_rework_full_path_code_green_through_security_to_complete() -> None:
    sm = _make_sm_at("CODE_GREEN")
    sm.advance_to("REVIEW")
    sm.advance_to("SECURITY")
    sm.advance_to("DOCUMENT")
    sm.advance_to("COMPLETE")
    assert sm.current_state == "COMPLETE"


def test_review_rework_review_state_is_present_in_linear_flow() -> None:
    from aignt_os.state_machine import LINEAR_STATE_FLOW

    assert "REVIEW" in LINEAR_STATE_FLOW
    assert "CODE_GREEN" in LINEAR_STATE_FLOW
    review_idx = LINEAR_STATE_FLOW.index("REVIEW")
    code_green_idx = LINEAR_STATE_FLOW.index("CODE_GREEN")
    assert code_green_idx < review_idx


def test_review_rework_security_follows_review_in_linear_flow() -> None:
    from aignt_os.state_machine import LINEAR_STATE_FLOW

    review_idx = LINEAR_STATE_FLOW.index("REVIEW")
    security_idx = LINEAR_STATE_FLOW.index("SECURITY")
    assert security_idx == review_idx + 1
