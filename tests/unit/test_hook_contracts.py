from __future__ import annotations

import pytest


def test_hook_config_rejects_invalid_point() -> None:
    from pydantic import ValidationError
    from synapse_os.runtime_contracts import HookConfig

    with pytest.raises(ValidationError):
        HookConfig(point="invalid_point", handler="some.module.handle")


def test_hook_config_defaults() -> None:
    from synapse_os.runtime_contracts import HookConfig

    h = HookConfig(point="pre_step", handler="some.module.handle")
    assert h.failure_mode == "supervisor_delegate"
    assert h.enabled is True


def test_hook_config_hard_fail_accepted() -> None:
    from synapse_os.runtime_contracts import HookConfig

    h = HookConfig(point="post_step", handler="a.b.c", failure_mode="hard_fail")
    assert h.failure_mode == "hard_fail"


def test_hook_context_metadata_defaults_to_empty() -> None:
    from synapse_os.runtime_contracts import HookContext

    ctx = HookContext(run_id="r1")
    assert ctx.metadata == {}
    assert ctx.step_name is None
    assert ctx.current_state is None


def test_hook_context_accepts_all_optional_fields() -> None:
    from synapse_os.runtime_contracts import HookContext, ToolSpec

    ts = ToolSpec(name="test-tool", capabilities=("generate",))

    ctx = HookContext(
        run_id="r1",
        step_name="PLAN",
        current_state="SPEC_VALIDATION",
        workspace_path="/tmp/ws",
        metadata={"key": "value"},
        tool_spec=ts,
    )
    assert ctx.step_name == "PLAN"
    assert ctx.metadata == {"key": "value"}
    assert ctx.tool_spec is not None


def test_hook_result_defaults() -> None:
    from synapse_os.runtime_contracts import HookResult

    r = HookResult(allowed=True)
    assert r.context_patch is None
    assert r.reason is None


def test_hook_result_allowed_false_with_reason() -> None:
    from synapse_os.runtime_contracts import HookResult

    r = HookResult(allowed=False, reason="permission denied")
    assert not r.allowed
    assert r.reason == "permission denied"


def test_hook_config_rejects_invalid_failure_mode() -> None:
    from pydantic import ValidationError
    from synapse_os.runtime_contracts import HookConfig

    with pytest.raises(ValidationError):
        HookConfig(point="pre_step", handler="a.b.c", failure_mode="log_and_continue")


def test_hook_config_rejects_empty_handler() -> None:
    from pydantic import ValidationError
    from synapse_os.runtime_contracts import HookConfig

    with pytest.raises(ValidationError):
        HookConfig(point="pre_step", handler="")


def test_hook_result_rejects_non_bool_allowed() -> None:
    from pydantic import ValidationError
    from synapse_os.runtime_contracts import HookResult

    with pytest.raises(ValidationError):
        HookResult(allowed="true")
