from __future__ import annotations

import logging
import sys
import types

import pytest

from synapse_os.hooks import HookDispatcher, HookRejectedError
from synapse_os.runtime_contracts import HookConfig, HookContext, HookResult


def _make_handler(allowed=True, reason=None, context_patch=None):
    def handler(ctx):
        return HookResult(allowed=allowed, reason=reason, context_patch=context_patch)

    return handler


class TestHookDispatcherMerge:
    def test_empty_hooks(self) -> None:
        d = HookDispatcher()
        assert d.hooks_active == []

    def test_global_only(self) -> None:
        global_hooks = [HookConfig(point="pre_step", handler="os.path.join")]
        d = HookDispatcher(global_hooks=global_hooks)
        assert len(d.hooks_active) == 1
        assert "pre_step:os.path.join" in d.hooks_active

    def test_spec_only(self) -> None:
        spec_hooks = [HookConfig(point="post_step", handler="os.path.join")]
        d = HookDispatcher(spec_hooks=spec_hooks)
        assert len(d.hooks_active) == 1
        assert "post_step:os.path.join" in d.hooks_active

    def test_merge_global_and_spec(self) -> None:
        global_hooks = [HookConfig(point="pre_step", handler="os.path.join")]
        spec_hooks = [HookConfig(point="post_step", handler="os.path.join")]
        d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
        assert len(d.hooks_active) == 2

    def test_spec_disable_removes_global(self) -> None:
        global_hooks = [HookConfig(point="pre_step", handler="os.path.join")]
        spec_hooks = [HookConfig(point="pre_step", handler="os.path.join", enabled=False)]
        d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
        assert d.hooks_active == []

    def test_spec_disable_only_by_handler_and_point(self) -> None:
        global_hooks = [
            HookConfig(point="pre_step", handler="os.path.join"),
            HookConfig(point="post_step", handler="os.path.join"),
        ]
        spec_hooks = [HookConfig(point="pre_step", handler="os.path.join", enabled=False)]
        d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
        assert len(d.hooks_active) == 1
        assert "post_step:os.path.join" in d.hooks_active

    def test_spec_enabled_adds_extra(self) -> None:
        global_hooks = [HookConfig(point="pre_step", handler="os.path.join")]
        spec_hooks = [HookConfig(point="pre_step", handler="os.path.dirname")]
        d = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
        assert len(d.hooks_active) == 2


class TestHookDispatcherLoadHandlers:
    def test_valid_dotted_path(self) -> None:
        global_hooks = [HookConfig(point="pre_step", handler="os.path.join")]
        d = HookDispatcher(global_hooks=global_hooks)
        assert len(d.hooks_active) == 1

    def test_invalid_module_hard_fail(self) -> None:
        global_hooks = [
            HookConfig(
                point="pre_step",
                handler="nonexistent_module.func",
                failure_mode="hard_fail",
            )
        ]
        with pytest.raises(RuntimeError, match="nonexistent_module.func"):
            HookDispatcher(global_hooks=global_hooks)

    def test_invalid_module_supervisor_delegate(self, caplog) -> None:
        global_hooks = [
            HookConfig(
                point="pre_step",
                handler="nonexistent_module.func",
                failure_mode="supervisor_delegate",
            )
        ]
        with caplog.at_level(logging.WARNING):
            d = HookDispatcher(global_hooks=global_hooks)
        assert d.hooks_active == []
        assert any("nonexistent_module" in r.message for r in caplog.records)

    def test_invalid_func_name_hard_fail(self) -> None:
        global_hooks = [
            HookConfig(
                point="pre_step",
                handler="os.nonexistent_func",
                failure_mode="hard_fail",
            )
        ]
        with pytest.raises(RuntimeError, match="os.nonexistent_func"):
            HookDispatcher(global_hooks=global_hooks)

    def test_invalid_func_name_supervisor_delegate(self, caplog) -> None:
        global_hooks = [
            HookConfig(
                point="pre_step",
                handler="os.nonexistent_func",
                failure_mode="supervisor_delegate",
            )
        ]
        with caplog.at_level(logging.WARNING):
            d = HookDispatcher(global_hooks=global_hooks)
        assert d.hooks_active == []

    def test_no_dot_in_handler(self) -> None:
        global_hooks = [HookConfig(point="pre_step", handler="nodots", failure_mode="hard_fail")]
        with pytest.raises(RuntimeError, match="dotted path"):
            HookDispatcher(global_hooks=global_hooks)


class TestHookDispatcherDispatchPre:
    def test_allowed_passes_through(self) -> None:
        h = _make_handler(allowed=True)
        mod = types.ModuleType("test_hook_mod")
        mod.handle = h
        sys.modules["test_hook_mod"] = mod
        try:
            hooks = [HookConfig(point="pre_step", handler="test_hook_mod.handle")]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            result = d.dispatch_pre("pre_step", ctx)
            assert result is ctx
        finally:
            del sys.modules["test_hook_mod"]

    def test_hard_fail_rejection_raises(self) -> None:
        h = _make_handler(allowed=False, reason="blocked")
        mod = types.ModuleType("test_hook_mod2")
        mod.handle = h
        sys.modules["test_hook_mod2"] = mod
        try:
            hooks = [
                HookConfig(
                    point="pre_step",
                    handler="test_hook_mod2.handle",
                    failure_mode="hard_fail",
                )
            ]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            with pytest.raises(HookRejectedError, match="Hook rejected step 'PLAN'"):
                d.dispatch_pre("pre_step", ctx)
        finally:
            del sys.modules["test_hook_mod2"]

    def test_supervisor_delegate_rejection_returns_context(self) -> None:
        h = _make_handler(allowed=False, reason="needs review")
        mod = types.ModuleType("test_hook_mod3")
        mod.handle = h
        sys.modules["test_hook_mod3"] = mod
        try:
            hooks = [
                HookConfig(
                    point="pre_step",
                    handler="test_hook_mod3.handle",
                    failure_mode="supervisor_delegate",
                )
            ]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            result = d.dispatch_pre("pre_step", ctx)
            assert result is ctx
        finally:
            del sys.modules["test_hook_mod3"]

    def test_context_patch_applies(self) -> None:
        h = _make_handler(allowed=True, context_patch={"extra": "value"})
        mod = types.ModuleType("test_hook_mod4")
        mod.handle = h
        sys.modules["test_hook_mod4"] = mod
        try:
            hooks = [HookConfig(point="pre_step", handler="test_hook_mod4.handle")]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            result = d.dispatch_pre("pre_step", ctx)
            assert result.metadata["extra"] == "value"
        finally:
            del sys.modules["test_hook_mod4"]

    def test_handler_exception_hard_fail_raises(self) -> None:
        def failing_handler(ctx):
            raise ValueError("boom")

        mod = types.ModuleType("test_hook_mod5")
        mod.handle = failing_handler
        sys.modules["test_hook_mod5"] = mod
        try:
            hooks = [
                HookConfig(
                    point="pre_step",
                    handler="test_hook_mod5.handle",
                    failure_mode="hard_fail",
                )
            ]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            with pytest.raises(HookRejectedError, match="boom"):
                d.dispatch_pre("pre_step", ctx)
        finally:
            del sys.modules["test_hook_mod5"]

    def test_handler_exception_supervisor_delegate_continues(self) -> None:
        def failing_handler(ctx):
            raise ValueError("boom")

        mod = types.ModuleType("test_hook_mod6")
        mod.handle = failing_handler
        sys.modules["test_hook_mod6"] = mod
        try:
            hooks = [
                HookConfig(
                    point="pre_step",
                    handler="test_hook_mod6.handle",
                    failure_mode="supervisor_delegate",
                )
            ]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            result = d.dispatch_pre("pre_step", ctx)
            assert result is ctx
        finally:
            del sys.modules["test_hook_mod6"]


class TestHookDispatcherDispatchPost:
    def test_post_handler_called(self) -> None:
        calls = []

        def post_handler(ctx):
            calls.append(ctx.run_id)

        mod = types.ModuleType("test_hook_mod7")
        mod.handle = post_handler
        sys.modules["test_hook_mod7"] = mod
        try:
            hooks = [HookConfig(point="post_step", handler="test_hook_mod7.handle")]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            d.dispatch_post("post_step", ctx)
            d.join_post_handlers(timeout=5)
            assert calls == ["r1"]
        finally:
            del sys.modules["test_hook_mod7"]

    def test_post_exception_does_not_propagate(self, caplog) -> None:
        def failing_handler(ctx):
            raise ValueError("post boom")

        mod = types.ModuleType("test_hook_mod8")
        mod.handle = failing_handler
        sys.modules["test_hook_mod8"] = mod
        try:
            hooks = [HookConfig(point="post_step", handler="test_hook_mod8.handle")]
            d = HookDispatcher(global_hooks=hooks)
            ctx = HookContext(run_id="r1", step_name="PLAN")
            with caplog.at_level(logging.WARNING):
                d.dispatch_post("post_step", ctx)
                d.join_post_handlers(timeout=5)
            assert any(
                "post boom" in r.message or "test_hook_mod8" in r.message for r in caplog.records
            )
        finally:
            del sys.modules["test_hook_mod8"]

    def test_no_handlers_does_nothing(self) -> None:
        d = HookDispatcher()
        ctx = HookContext(run_id="r1")
        d.dispatch_post("post_step", ctx)
        d.join_post_handlers()
