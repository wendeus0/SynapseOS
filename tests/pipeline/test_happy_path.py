"""End-to-end pipeline tests using fake executors.

These tests exercise the full AIgnt-Synapse-Flow pipeline — the engine própria
de pipeline do AIgnt OS — from SPEC validation through to TEST_RED, using
in-memory fake executors and temporary SPEC files. No real subprocesses or
external tools are invoked.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_VALID_SPEC_CONTENT = """\
---
id: F-pipeline-e2e-fixture
type: feature
summary: End-to-end pipeline fixture spec.
inputs:
  - raw_request
outputs:
  - plan_md
  - tests_md
acceptance_criteria:
  - Pipeline must execute SPEC_VALIDATION before PLAN.
  - Pipeline must execute PLAN before TEST_RED.
non_goals:
  - Real subprocess execution.
  - Worker or scheduler integration.
---

# Contexto

Fixture para testes end-to-end da pipeline AIgnt-Synapse-Flow.

# Objetivo

Executar a pipeline completa ate TEST_RED com executores fake e verificar
os hand-offs entre cada step.
"""

_INVALID_SPEC_CONTENT = "# Sem front matter YAML\n"


def _make_spec(tmp_path: Path, content: str) -> Path:
    spec = tmp_path / "SPEC.md"
    spec.write_text(content, encoding="utf-8")
    return spec


def _pipeline_module():
    from importlib import import_module

    return import_module("aignt_os.pipeline")


class _FakeExecutor:
    """Records every call and returns a fixed artifact set."""

    def __init__(self, **artifacts: str) -> None:
        self._artifacts = artifacts
        self.calls: list[tuple[str, str | None]] = []

    def execute(self, step, context):  # type: ignore[no-untyped-def]
        spec_id = context.validated_spec.metadata.id if context.validated_spec else None
        self.calls.append((step.state, spec_id))
        pipeline = _pipeline_module()
        return pipeline.StepExecutionResult(artifacts=dict(self._artifacts))


class _FailingExecutor:
    """Always raises PipelineExecutionError."""

    def execute(self, step, context):  # type: ignore[no-untyped-def]
        pipeline = _pipeline_module()
        raise pipeline.PipelineExecutionError(f"Fake failure at {step.state}")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_pipeline_runs_spec_validation_before_any_executor(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")
    test_exec = _FakeExecutor(tests_md="# Tests")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec, "TEST_RED": test_exec})
    context = engine.run(spec_path)

    assert "SPEC_VALIDATION" in context.step_history
    assert context.step_history.index("SPEC_VALIDATION") < context.step_history.index("PLAN")
    assert context.step_history.index("PLAN") < context.step_history.index("TEST_RED")


def test_pipeline_populates_spec_id_artifact_from_validated_spec(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")
    test_exec = _FakeExecutor(tests_md="# Tests")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec, "TEST_RED": test_exec})
    context = engine.run(spec_path)

    assert context.artifacts["spec_id"] == "F-pipeline-e2e-fixture"
    assert context.artifacts["spec_summary"] == "End-to-end pipeline fixture spec."


def test_pipeline_executor_receives_validated_spec_in_context(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")
    test_exec = _FakeExecutor(tests_md="# Tests")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec, "TEST_RED": test_exec})
    engine.run(spec_path)

    assert plan_exec.calls == [("PLAN", "F-pipeline-e2e-fixture")]
    assert test_exec.calls == [("TEST_RED", "F-pipeline-e2e-fixture")]


def test_pipeline_merges_all_executor_artifacts_into_context(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan", extra_plan_note="noted")
    test_exec = _FakeExecutor(tests_md="# Tests")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec, "TEST_RED": test_exec})
    context = engine.run(spec_path)

    assert context.artifacts["plan_md"] == "# Plan"
    assert context.artifacts["extra_plan_note"] == "noted"
    assert context.artifacts["tests_md"] == "# Tests"


def test_pipeline_stop_at_plan_does_not_invoke_test_red_executor(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")
    test_exec = _FakeExecutor(tests_md="# Tests")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec, "TEST_RED": test_exec})
    context = engine.run(spec_path, stop_at="PLAN")

    assert context.current_state == "PLAN"
    assert context.step_history == ["SPEC_VALIDATION", "PLAN"]
    assert "tests_md" not in context.artifacts
    assert test_exec.calls == []


def test_pipeline_context_records_spec_path(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")
    test_exec = _FakeExecutor(tests_md="# Tests")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec, "TEST_RED": test_exec})
    context = engine.run(spec_path)

    assert context.spec_path == spec_path


# ---------------------------------------------------------------------------
# SPEC validation failure blocks pipeline
# ---------------------------------------------------------------------------


def test_pipeline_raises_spec_validation_error_for_invalid_spec(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _INVALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec})

    with pytest.raises(pipeline.SpecValidationError):
        engine.run(spec_path)


def test_pipeline_does_not_invoke_plan_executor_when_spec_is_invalid(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _INVALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec})

    with pytest.raises(pipeline.SpecValidationError):
        engine.run(spec_path)

    assert plan_exec.calls == []


def test_pipeline_state_machine_remains_at_spec_validation_after_spec_error(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _INVALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec})

    with pytest.raises(pipeline.SpecValidationError):
        engine.run(spec_path)

    assert engine.state_machine.current_state == "SPEC_VALIDATION"


# ---------------------------------------------------------------------------
# Missing executor raises PipelineExecutionError
# ---------------------------------------------------------------------------


def test_pipeline_raises_execution_error_when_test_red_executor_is_missing(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_exec})

    with pytest.raises(pipeline.PipelineExecutionError, match="TEST_RED"):
        engine.run(spec_path)


def test_pipeline_raises_execution_error_when_all_executors_are_missing(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)

    engine = pipeline.PipelineEngine(executors={})

    with pytest.raises(pipeline.PipelineExecutionError, match="PLAN"):
        engine.run(spec_path)


# ---------------------------------------------------------------------------
# Executor error propagation
# ---------------------------------------------------------------------------


def test_pipeline_propagates_exception_from_failing_plan_executor(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)

    engine = pipeline.PipelineEngine(executors={"PLAN": _FailingExecutor()})

    with pytest.raises(pipeline.PipelineExecutionError, match="PLAN"):
        engine.run(spec_path)


# ---------------------------------------------------------------------------
# stop_at validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stop_at",
    ["SPEC_VALIDATION", "PLAN", "TEST_RED", "CODE_GREEN", "REVIEW", "SECURITY"],
)
def test_pipeline_accepts_supported_stop_at_values(tmp_path: Path, stop_at: str) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)
    plan_exec = _FakeExecutor(plan_md="# Plan")
    test_exec = _FakeExecutor(tests_md="# Tests")
    code_exec = _FakeExecutor(code_md="# Code")
    review_exec = _FakeExecutor(review_md="# Review")
    security_exec = _FakeExecutor(security_md="# Security")

    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_exec,
            "TEST_RED": test_exec,
            "CODE_GREEN": code_exec,
            "REVIEW": review_exec,
            "SECURITY": security_exec,
        }
    )
    context = engine.run(spec_path, stop_at=stop_at)

    assert context.current_state == stop_at


@pytest.mark.parametrize(
    "invalid_stop_at",
    ["COMPLETE", "REQUEST", "INVALID"],
)
def test_pipeline_rejects_unsupported_stop_at_values(tmp_path: Path, invalid_stop_at: str) -> None:
    pipeline = _pipeline_module()
    spec_path = _make_spec(tmp_path, _VALID_SPEC_CONTENT)

    engine = pipeline.PipelineEngine(executors={})

    with pytest.raises(ValueError, match="stop_at"):
        engine.run(spec_path, stop_at=invalid_stop_at)
