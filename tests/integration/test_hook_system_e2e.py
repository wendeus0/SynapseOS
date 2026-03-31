from __future__ import annotations

import types
import sys
import time
from pathlib import Path

import pytest

from synapse_os.config import AppSettings
from synapse_os.hooks import HookDispatcher, HookRejectedError
from synapse_os.pipeline import (
    PipelineContext,
    PipelineEngine,
    PipelineState,
    StepExecutionResult,
)
from synapse_os.runtime_contracts import HookConfig, HookContext
from synapse_os.specs import validate_spec_file
from synapse_os.state_machine import SynapseStateMachine


class MockStepExecutor:
    def execute(self, step, context):
        return StepExecutionResult(
            clean_output=f"Executed {step.state}",
            return_code=0,
        )


class TestHookSystemE2E:
    def _make_engine_with_executors(self, hook_dispatcher=None, settings=None):
        sm = SynapseStateMachine()
        sm.advance_to(PipelineState.SPEC_DISCOVERY)
        sm.advance_to(PipelineState.SPEC_NORMALIZATION)
        sm.advance_to(PipelineState.SPEC_VALIDATION)
        executors = {
            state: MockStepExecutor()
            for state in [
                "PLAN",
                "TEST_RED",
                "CODE_GREEN",
                "QUALITY_GATE",
                "REVIEW",
                "SECURITY",
                "DOCUMENT",
            ]
        }
        return PipelineEngine(
            settings=settings or AppSettings(),
            state_machine=sm,
            hook_dispatcher=hook_dispatcher,
            executors=executors,
        )

    def _write_spec(self, tmp_path, spec_id="F1"):
        spec_path = tmp_path / "SPEC.md"
        spec_path.write_text(
            f"---\nid: {spec_id}\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
        )
        return spec_path

    def test_full_pipeline_with_pre_step_hook(self, tmp_path) -> None:
        mod = types.ModuleType("test_e2e_hook1")
        mod.handle = lambda ctx: type(
            "R", (), {"allowed": True, "reason": None, "context_patch": None}
        )()
        sys.modules["test_e2e_hook1"] = mod
        try:
            hooks = [HookConfig(point="pre_step", handler="test_e2e_hook1.handle")]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine_with_executors(hook_dispatcher=dispatcher)
            spec_path = self._write_spec(tmp_path)

            ctx = engine.run(spec_path, stop_at="PLAN")
            assert ctx.current_state == PipelineState.PLAN
            assert "pre_step:test_e2e_hook1.handle" in ctx.hooks_active
        finally:
            del sys.modules["test_e2e_hook1"]

    def test_pre_step_hook_blocks_pipeline(self, tmp_path) -> None:
        mod = types.ModuleType("test_e2e_hook2")
        mod.handle = lambda ctx: type(
            "R", (), {"allowed": False, "reason": "policy", "context_patch": None}
        )()
        sys.modules["test_e2e_hook2"] = mod
        try:
            hooks = [
                HookConfig(
                    point="pre_step",
                    handler="test_e2e_hook2.handle",
                    failure_mode="hard_fail",
                )
            ]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine_with_executors(hook_dispatcher=dispatcher)
            spec_path = self._write_spec(tmp_path)

            from synapse_os.supervisor import RetryableStepError

            with pytest.raises(RetryableStepError):
                engine.run(spec_path, stop_at="PLAN")
        finally:
            del sys.modules["test_e2e_hook2"]

    def test_post_hook_runs_in_background(self, tmp_path) -> None:
        results = []

        def post_handler(ctx):
            time.sleep(0.1)
            results.append(ctx.step_name)

        mod = types.ModuleType("test_e2e_hook3")
        mod.handle = post_handler
        sys.modules["test_e2e_hook3"] = mod
        try:
            hooks = [HookConfig(point="post_step", handler="test_e2e_hook3.handle")]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine_with_executors(hook_dispatcher=dispatcher)
            spec_path = self._write_spec(tmp_path)

            ctx = engine.run(spec_path, stop_at="PLAN")
            dispatcher.join_post_handlers(timeout=5)
            assert "PLAN" in results
        finally:
            del sys.modules["test_e2e_hook3"]

    def test_state_transition_hooks(self, tmp_path) -> None:
        transitions = []

        def pre_transition(ctx):
            transitions.append(f"pre:{ctx.current_state}")
            return type(
                "R", (), {"allowed": True, "reason": None, "context_patch": None}
            )()

        def post_transition(ctx):
            transitions.append(f"post:{ctx.current_state}")

        mod_pre = types.ModuleType("test_e2e_hook4a")
        mod_post = types.ModuleType("test_e2e_hook4b")
        mod_pre.handle = pre_transition
        mod_post.handle = post_transition
        sys.modules["test_e2e_hook4a"] = mod_pre
        sys.modules["test_e2e_hook4b"] = mod_post
        try:
            hooks = [
                HookConfig(
                    point="pre_state_transition", handler="test_e2e_hook4a.handle"
                ),
                HookConfig(
                    point="post_state_transition", handler="test_e2e_hook4b.handle"
                ),
            ]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine_with_executors(hook_dispatcher=dispatcher)
            spec_path = self._write_spec(tmp_path)

            ctx = engine.run(spec_path, stop_at="PLAN")
            dispatcher.join_post_handlers(timeout=5)
            assert any("pre:SPEC_VALIDATION" in t for t in transitions)
            assert any("post:PLAN" in t for t in transitions)
        finally:
            del sys.modules["test_e2e_hook4a"]
            del sys.modules["test_e2e_hook4b"]

    def test_context_patch_from_hook(self, tmp_path) -> None:
        def patching_handler(ctx):
            return type(
                "R",
                (),
                {"allowed": True, "reason": None, "context_patch": {"cost_limit": 100}},
            )()

        mod = types.ModuleType("test_e2e_hook5")
        mod.handle = patching_handler
        sys.modules["test_e2e_hook5"] = mod
        try:
            hooks = [HookConfig(point="pre_step", handler="test_e2e_hook5.handle")]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine_with_executors(hook_dispatcher=dispatcher)
            spec_path = self._write_spec(tmp_path)

            ctx = engine.run(spec_path, stop_at="PLAN")
            assert ctx.current_state == PipelineState.PLAN
        finally:
            del sys.modules["test_e2e_hook5"]

    def test_spec_hook_disables_global_hook(self, tmp_path) -> None:
        mod = types.ModuleType("test_e2e_hook6")
        mod.handle = lambda ctx: type(
            "R", (), {"allowed": True, "reason": None, "context_patch": None}
        )()
        sys.modules["test_e2e_hook6"] = mod
        try:
            global_hooks = [
                HookConfig(point="pre_step", handler="test_e2e_hook6.handle")
            ]
            spec_hooks = [
                HookConfig(
                    point="pre_step", handler="test_e2e_hook6.handle", enabled=False
                )
            ]
            dispatcher = HookDispatcher(
                global_hooks=global_hooks, spec_hooks=spec_hooks
            )
            engine = self._make_engine_with_executors(hook_dispatcher=dispatcher)
            spec_path = self._write_spec(tmp_path)

            ctx = engine.run(spec_path, stop_at="PLAN")
            assert ctx.hooks_active == []
        finally:
            del sys.modules["test_e2e_hook6"]

    def test_invalid_handler_hard_fail_stops_at_startup(self) -> None:
        hooks = [
            HookConfig(
                point="pre_step",
                handler="nonexistent.module.func",
                failure_mode="hard_fail",
            )
        ]
        with pytest.raises(RuntimeError, match="nonexistent.module.func"):
            HookDispatcher(global_hooks=hooks)

    def test_invalid_handler_supervisor_delegate_continues(self, caplog) -> None:
        hooks = [
            HookConfig(
                point="pre_step",
                handler="nonexistent.module.func",
                failure_mode="supervisor_delegate",
            )
        ]
        import logging

        with caplog.at_level(logging.WARNING):
            dispatcher = HookDispatcher(global_hooks=hooks)
        assert dispatcher.hooks_active == []
