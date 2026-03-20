from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


def _pipeline_module():
    return import_module("synapse_os.pipeline")


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


class _FlakyExecutor:
    def __init__(self, *, fail_times: int, artifact_key: str, artifact_value: str) -> None:
        self.fail_times = fail_times
        self.artifact_key = artifact_key
        self.artifact_value = artifact_value
        self.calls = 0

    def execute(self, step, context):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls <= self.fail_times:
            supervisor = import_module("synapse_os.supervisor")
            raise supervisor.RetryableStepError(f"temporary failure at {step.state}")
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


def test_pipeline_engine_exposes_run_context_to_executors(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")

    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_executor,
            "TEST_RED": _RecordingExecutor(artifact_key="tests_md", artifact_value="red"),
        }
    )

    context = engine.run(spec_path, stop_at="PLAN", run_id="run-123", initiated_by="operator-a")

    assert context.run_context.run_id == "run-123"
    assert context.run_context.initiated_by == "operator-a"
    assert context.run_context.workspace.root_path == tmp_path
    assert context.run_context.workspace.spec_path == spec_path.resolve()
    assert plan_executor.calls == [("PLAN", "F06-fixture")]


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


def test_pipeline_engine_can_retry_code_green_and_continue_to_security(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")
    test_red_executor = _RecordingExecutor(artifact_key="tests_md", artifact_value="red")
    code_green_executor = _FlakyExecutor(
        fail_times=1,
        artifact_key="code_md",
        artifact_value="green",
    )
    review_executor = _RecordingExecutor(artifact_key="review_md", artifact_value="review")
    security_executor = _RecordingExecutor(
        artifact_key="security_md",
        artifact_value="security",
    )
    supervisor = import_module("synapse_os.supervisor")

    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_executor,
            "TEST_RED": test_red_executor,
            "CODE_GREEN": code_green_executor,
            "QUALITY_GATE": _RecordingExecutor(
                artifact_key="quality_gate_md", artifact_value="gate"
            ),
            "REVIEW": review_executor,
            "SECURITY": security_executor,
        },
        supervisor=supervisor.Supervisor(max_retries=2),
    )

    context = engine.run(spec_path, stop_at="SECURITY")

    assert context.current_state == "SECURITY"
    assert context.step_history == [
        "SPEC_VALIDATION",
        "PLAN",
        "TEST_RED",
        "CODE_GREEN",
        "QUALITY_GATE",
        "REVIEW",
        "SECURITY",
    ]
    assert context.supervisor_decisions == ["retry:CODE_GREEN"]
    assert code_green_executor.calls == 2


def test_pipeline_engine_can_stop_after_document(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")
    test_red_executor = _RecordingExecutor(artifact_key="tests_md", artifact_value="red")
    code_green_executor = _RecordingExecutor(artifact_key="code_md", artifact_value="green")
    review_executor = _RecordingExecutor(artifact_key="review_md", artifact_value="review")
    security_executor = _RecordingExecutor(
        artifact_key="security_md",
        artifact_value="security",
    )
    document_executor = _RecordingExecutor(
        artifact_key="run_report_md",
        artifact_value="# RUN_REPORT\n",
    )

    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_executor,
            "TEST_RED": test_red_executor,
            "CODE_GREEN": code_green_executor,
            "QUALITY_GATE": _RecordingExecutor(
                artifact_key="quality_gate_md", artifact_value="gate"
            ),
            "REVIEW": review_executor,
            "SECURITY": security_executor,
            "DOCUMENT": document_executor,
        }
    )

    context = engine.run(spec_path, stop_at="DOCUMENT")

    assert engine.state_machine.current_state == "DOCUMENT"
    assert context.current_state == "DOCUMENT"
    assert context.step_history == [
        "SPEC_VALIDATION",
        "PLAN",
        "TEST_RED",
        "CODE_GREEN",
        "QUALITY_GATE",
        "REVIEW",
        "SECURITY",
        "DOCUMENT",
    ]
    assert context.artifacts["run_report_md"] == "# RUN_REPORT\n"


def test_pipeline_engine_can_return_from_review_to_code_green(tmp_path: Path) -> None:
    pipeline = _pipeline_module()
    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    plan_executor = _RecordingExecutor(artifact_key="plan_md", artifact_value="plan")
    test_red_executor = _RecordingExecutor(artifact_key="tests_md", artifact_value="red")
    code_green_executor = _RecordingExecutor(artifact_key="code_md", artifact_value="green")
    security_executor = _RecordingExecutor(
        artifact_key="security_md",
        artifact_value="security",
    )
    supervisor = import_module("synapse_os.supervisor")

    class _RejectingReviewExecutor:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, step, context):  # type: ignore[no-untyped-def]
            self.calls += 1
            if self.calls == 1:
                raise supervisor.ReviewRejectedError("changes requested")
            return pipeline.StepExecutionResult(artifacts={"review_md": "approved"})

    review_executor = _RejectingReviewExecutor()
    engine = pipeline.PipelineEngine(
        executors={
            "PLAN": plan_executor,
            "TEST_RED": test_red_executor,
            "CODE_GREEN": code_green_executor,
            "QUALITY_GATE": _RecordingExecutor(
                artifact_key="quality_gate_md", artifact_value="gate"
            ),
            "REVIEW": review_executor,
            "SECURITY": security_executor,
        },
        supervisor=supervisor.Supervisor(max_retries=1),
    )

    context = engine.run(spec_path, stop_at="SECURITY")

    assert context.current_state == "SECURITY"
    assert context.step_history == [
        "SPEC_VALIDATION",
        "PLAN",
        "TEST_RED",
        "CODE_GREEN",
        "QUALITY_GATE",
        "REVIEW",
        "CODE_GREEN",
        "QUALITY_GATE",
        "REVIEW",
        "SECURITY",
    ]
    assert context.supervisor_decisions == ["return_to_code_green:REVIEW"]
