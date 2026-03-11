from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


def _write_valid_spec(path: Path) -> None:
    path.write_text(
        """---
id: F07-fixture
type: feature
summary: Fixture spec for pipeline persistence tests.
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


class _PlanExecutor:
    def execute(self, step, context):  # type: ignore[no-untyped-def]
        del step, context
        pipeline = import_module("aignt_os.pipeline")
        return pipeline.StepExecutionResult(
            artifacts={"plan_md": "# Generated Plan\n"},
            raw_output="RAW PLAN\n",
            clean_output="# Generated Plan\n",
        )


def test_persisted_pipeline_records_steps_events_and_artifacts_until_plan(
    tmp_path: Path,
) -> None:
    persistence = import_module("aignt_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={"PLAN": _PlanExecutor()},
    )

    context = runner.run(spec_path, stop_at="PLAN")

    assert context.run_id is not None
    run_record = repository.get_run(context.run_id)
    steps = repository.list_steps(context.run_id)
    events = repository.list_events(context.run_id)

    assert run_record.status == "completed"
    assert run_record.current_state == "PLAN"
    assert [step.state for step in steps] == ["SPEC_VALIDATION", "PLAN"]
    assert [event.event_type for event in events] == [
        "run_started",
        "step_completed",
        "step_completed",
        "run_completed",
    ]

    plan_step_dir = artifact_store.base_path / context.run_id / "PLAN"
    assert (plan_step_dir / "raw.txt").read_text(encoding="utf-8") == "RAW PLAN\n"
    assert (plan_step_dir / "clean.txt").read_text(encoding="utf-8") == "# Generated Plan\n"
    assert (plan_step_dir / "plan_md.txt").read_text(encoding="utf-8") == "# Generated Plan\n"


def test_persisted_pipeline_marks_failed_run_when_spec_validation_blocks_plan(
    tmp_path: Path,
) -> None:
    persistence = import_module("aignt_os.persistence")
    pipeline = import_module("aignt_os.pipeline")

    spec_path = tmp_path / "SPEC.md"
    _write_invalid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={"PLAN": _PlanExecutor()},
    )

    with pytest.raises(pipeline.SpecValidationError, match="front matter YAML"):
        runner.run(spec_path, stop_at="PLAN")

    runs = repository.list_runs()
    assert len(runs) == 1
    run_record = runs[0]
    events = repository.list_events(run_record.run_id)

    assert run_record.status == "failed"
    assert run_record.current_state == "SPEC_VALIDATION"
    assert run_record.failure_message is not None
    assert [event.event_type for event in events] == ["run_started", "run_failed"]
    assert not (artifact_store.base_path / run_record.run_id / "PLAN").exists()


def test_persisted_pipeline_records_supervisor_decision_events(tmp_path: Path) -> None:
    persistence = import_module("aignt_os.persistence")
    pipeline = import_module("aignt_os.pipeline")
    supervisor = import_module("aignt_os.supervisor")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")

    class _FlakyCodeGreenExecutor:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, step, context):  # type: ignore[no-untyped-def]
            self.calls += 1
            if self.calls == 1:
                raise supervisor.RetryableStepError("temporary failure")
            return pipeline.StepExecutionResult(
                artifacts={"code_md": "# Green\n"},
                raw_output="RAW GREEN\n",
                clean_output="# Green\n",
            )

    class _FixedExecutor:
        def __init__(self, artifact_name: str, content: str) -> None:
            self.artifact_name = artifact_name
            self.content = content

        def execute(self, step, context):  # type: ignore[no-untyped-def]
            return pipeline.StepExecutionResult(artifacts={self.artifact_name: self.content})

    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={
            "PLAN": _FixedExecutor("plan_md", "# Plan\n"),
            "TEST_RED": _FixedExecutor("tests_md", "# Tests\n"),
            "CODE_GREEN": _FlakyCodeGreenExecutor(),
            "REVIEW": _FixedExecutor("review_md", "# Review\n"),
            "SECURITY": _FixedExecutor("security_md", "# Security\n"),
        },
        supervisor=supervisor.Supervisor(max_retries=2),
    )

    context = runner.run(spec_path, stop_at="SECURITY")
    events = repository.list_events(context.run_id)

    assert [event.event_type for event in events] == [
        "run_started",
        "step_completed",
        "step_completed",
        "step_completed",
        "supervisor_decision",
        "step_completed",
        "step_completed",
        "step_completed",
        "run_completed",
    ]
    assert events[3].state == "TEST_RED"
    assert events[4].state == "CODE_GREEN"
    assert "retry" in events[4].message
