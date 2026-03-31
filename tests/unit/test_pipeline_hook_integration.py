from __future__ import annotations

import types
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from synapse_os.config import AppSettings
from synapse_os.hooks import HookDispatcher, HookRejectedError
from synapse_os.pipeline import (
    PipelineContext,
    PipelineEngine,
    PipelineStep,
    PipelineState,
    StepExecutionResult,
)
from synapse_os.runtime_contracts import HookConfig, HookContext
from synapse_os.state_machine import SynapseStateMachine


class TestPipelineHookIntegration:
    def _make_engine(self, hook_dispatcher=None, settings=None):
        sm = SynapseStateMachine()
        sm.advance_to(PipelineState.SPEC_DISCOVERY)
        sm.advance_to(PipelineState.SPEC_NORMALIZATION)
        sm.advance_to(PipelineState.SPEC_VALIDATION)
        return PipelineEngine(
            settings=settings or AppSettings(),
            state_machine=sm,
            hook_dispatcher=hook_dispatcher,
        )

    def test_hooks_active_populated_from_dispatcher(self, tmp_path) -> None:
        mod = types.ModuleType("test_int_hook")
        mod.handle = lambda ctx: type(
            "R", (), {"allowed": True, "reason": None, "context_patch": None}
        )()
        sys.modules["test_int_hook"] = mod
        try:
            hooks = [HookConfig(point="pre_step", handler="test_int_hook.handle")]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine(hook_dispatcher=dispatcher)

            spec_path = tmp_path / "SPEC.md"
            spec_path.write_text(
                "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
            )

            ctx = engine.run(spec_path, stop_at="SPEC_VALIDATION")
            assert "pre_step:test_int_hook.handle" in ctx.hooks_active
        finally:
            del sys.modules["test_int_hook"]

    def test_hooks_active_empty_without_dispatcher(self, tmp_path) -> None:
        engine = self._make_engine()
        spec_path = tmp_path / "SPEC.md"
        spec_path.write_text(
            "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
        )
        ctx = engine.run(spec_path, stop_at="SPEC_VALIDATION")
        assert ctx.hooks_active == []

    def test_pre_step_hook_rejection_raises(self, tmp_path) -> None:
        mod = types.ModuleType("test_int_hook2")
        mod.handle = lambda ctx: type(
            "R", (), {"allowed": False, "reason": "blocked", "context_patch": None}
        )()
        sys.modules["test_int_hook2"] = mod
        try:
            hooks = [
                HookConfig(
                    point="pre_step",
                    handler="test_int_hook2.handle",
                    failure_mode="hard_fail",
                )
            ]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine(hook_dispatcher=dispatcher)

            spec_path = tmp_path / "SPEC.md"
            spec_path.write_text(
                "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
            )

            from synapse_os.supervisor import RetryableStepError

            with pytest.raises(RetryableStepError, match="Hook rejected"):
                engine.run(spec_path, stop_at="PLAN")
        finally:
            del sys.modules["test_int_hook2"]

    def test_post_hook_does_not_block_execution(self, tmp_path) -> None:
        calls = []

        def post_handler(ctx):
            calls.append(ctx.run_id)
            raise ValueError("post error")

        mod = types.ModuleType("test_int_hook3")
        mod.handle = post_handler
        sys.modules["test_int_hook3"] = mod
        try:
            hooks = [HookConfig(point="post_step", handler="test_int_hook3.handle")]
            dispatcher = HookDispatcher(global_hooks=hooks)
            engine = self._make_engine(hook_dispatcher=dispatcher)

            spec_path = tmp_path / "SPEC.md"
            spec_path.write_text(
                "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
            )

            ctx = engine.run(spec_path, stop_at="SPEC_VALIDATION")
            dispatcher.join_post_handlers(timeout=5)
            assert calls == ["unknown"]
        finally:
            del sys.modules["test_int_hook3"]

    def test_spec_hooks_merge_with_global(self, tmp_path) -> None:
        mod = types.ModuleType("test_int_hook4")
        mod.handle = lambda ctx: type(
            "R", (), {"allowed": True, "reason": None, "context_patch": None}
        )()
        sys.modules["test_int_hook4"] = mod
        try:
            global_hooks = [HookConfig(point="pre_step", handler="test_int_hook4.handle")]
            spec_hooks = [HookConfig(point="post_step", handler="test_int_hook4.handle")]
            dispatcher = HookDispatcher(global_hooks=global_hooks, spec_hooks=spec_hooks)
            engine = self._make_engine(hook_dispatcher=dispatcher)

            spec_path = tmp_path / "SPEC.md"
            spec_path.write_text(
                "---\nid: F1\ntype: feature\nsummary: test\ninputs: [a]\noutputs: [b]\nacceptance_criteria: [c]\nnon_goals: []\n---\n\n# Contexto\ntest\n\n# Objetivo\ntest\n"
            )

            ctx = engine.run(spec_path, stop_at="SPEC_VALIDATION")
            assert len(ctx.hooks_active) == 2
        finally:
            del sys.modules["test_int_hook4"]
