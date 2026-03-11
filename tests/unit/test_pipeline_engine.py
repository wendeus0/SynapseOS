from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


def _pipeline_module():
    return import_module("aignt_os.pipeline")


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F06-fixture
type: feature
summary: Fixture spec for pipeline tests.
inputs:
  - raw_request
outputs:
  - plan_md
acceptance_criteria:
  - must validate
non_goals: []
---

# Contexto

Fixture context.

# Objetivo

Fixture objective.
""",
        encoding="utf-8",
    )


def _write_invalid_spec(path: Path) -> None:
    path.write_text("# Missing YAML front matter\n", encoding="utf-8")


class _RecordingExecutor:
    def __init__(self, *, artifact_key: str, artifact_value: str) -> None:
        self.artifact_key = artifact_key
        self.artifact_value = artifact_value
        self.calls: list[tuple[str, str | None]] = []

    def execute(self, step, context):  # type: ignore[no-untyped-def]
        validated_spec_id = None
        if context.validated_spec is not None:
            validated_spec_id = context.validated_spec.metadata.id
        self.calls.append((step.state, validated_spec_id))
        pipeline = _pipeline_module()
        return pipeline.StepExecutionResult(
            artifacts={self.artifact_key: self.artifact_value},
        )


def test_pipeline_engine_executes_linear_flow_until_test_red(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")
    test_red_executor = _RecordingExecutor(artifact_key="tests_md", artifact_value="red")

    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_executor,
            "TEST_RED": test_red_executor,
        }
    )

    context = engine.run(spec_path)

    assert engine.state_machine.current_state == "TEST_RED"
    assert context.current_state == "TEST_RED"
    assert context.step_history == ["SPEC_VALIDATION", "PLAN", "TEST_RED"]
    assert context.validated_spec is not None
    assert context.validated_spec.metadata.id == "F06-fixture"
    assert context.artifacts["spec_id"] == "F06-fixture"
    assert context.artifacts["spec_summary"] == "Fixture spec for pipeline tests."
    assert context.artifacts["plan_md"] == "plan"
    assert context.artifacts["tests_md"] == "red"
    assert plan_executor.calls == [("PLAN", "F06-fixture")]
    assert test_red_executor.calls == [("TEST_RED", "F06-fixture")]


def test_pipeline_engine_can_stop_after_plan(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")
    test_red_executor = _RecordingExecutor(artifact_key="tests_md", artifact_value="red")

    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_executor,
            "TEST_RED": test_red_executor,
        }
    )

    context = engine.run(spec_path, stop_at="PLAN")

    assert engine.state_machine.current_state == "PLAN"
    assert context.current_state == "PLAN"
    assert context.step_history == ["SPEC_VALIDATION", "PLAN"]
    assert context.artifacts["plan_md"] == "plan"
    assert "tests_md" not in context.artifacts
    assert plan_executor.calls == [("PLAN", "F06-fixture")]
    assert test_red_executor.calls == []


def test_pipeline_engine_can_stop_after_spec_validation(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_executor})

    context = engine.run(spec_path, stop_at="SPEC_VALIDATION")

    assert engine.state_machine.current_state == "SPEC_VALIDATION"
    assert context.current_state == "SPEC_VALIDATION"
    assert context.step_history == ["SPEC_VALIDATION"]
    assert context.artifacts["spec_id"] == "F06-fixture"
    assert "plan_md" not in context.artifacts
    assert plan_executor.calls == []


def test_pipeline_engine_blocks_plan_when_spec_is_invalid(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_invalid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_executor})

    with pytest.raises(pipeline.SpecValidationError, match="front matter YAML"):
        engine.run(spec_path)

    assert engine.state_machine.current_state == "SPEC_VALIDATION"
    assert plan_executor.calls == []


def test_pipeline_engine_fails_when_required_executor_is_missing(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")

    engine = pipeline.PipelineEngine(executors={"PLAN": plan_executor})

    with pytest.raises(pipeline.PipelineExecutionError, match="TEST_RED"):
        engine.run(spec_path)

    assert engine.state_machine.current_state == "TEST_RED"
    assert plan_executor.calls == [("PLAN", "F06-fixture")]
