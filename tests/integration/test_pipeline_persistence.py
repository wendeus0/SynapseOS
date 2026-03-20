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
        pipeline = import_module("synapse_os.pipeline")
        return pipeline.StepExecutionResult(
            artifacts={"plan_md": "# Generated Plan\n"},
            raw_output="RAW PLAN\n",
            clean_output="# Generated Plan\n",
            tool_name="fake-executor",
            return_code=0,
            duration_ms=45,
            timed_out=False,
        )


def test_persisted_pipeline_records_steps_events_and_artifacts_until_plan(
    tmp_path: Path,
) -> None:
    persistence = import_module("synapse_os.persistence")
    runtime_contracts = import_module("synapse_os.runtime_contracts")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")
    run_workspaces_root = tmp_path / "run-workspaces"
    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={"PLAN": _PlanExecutor()},
        workspace_provider=runtime_contracts.LocalWorkspaceProvider(tmp_path),
        run_workspace_root=run_workspaces_root,
    )

    context = runner.run(spec_path, stop_at="PLAN")

    assert context.run_id is not None
    run_record = repository.get_run(context.run_id)
    steps = repository.list_steps(context.run_id)
    events = repository.list_events(context.run_id)

    assert run_record.status == "completed"
    assert run_record.current_state == "PLAN"
    assert run_record.workspace_path == str(run_workspaces_root / context.run_id)
    assert context.run_context.workspace.root_path == run_workspaces_root / context.run_id
    assert (run_workspaces_root / context.run_id).is_dir()
    assert [step.state for step in steps] == ["SPEC_VALIDATION", "PLAN"]
    assert [event.event_type for event in events] == [
        "security_provenance_recorded",
        "run_context_initialized",
        "run_started",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
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
    persistence = import_module("synapse_os.persistence")
    pipeline = import_module("synapse_os.pipeline")

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
    assert [event.event_type for event in events] == [
        "security_provenance_recorded",
        "run_context_initialized",
        "run_started",
        "state_transitioned",
        "step_started",
        "run_failed",
    ]
    assert not (artifact_store.base_path / run_record.run_id / "PLAN").exists()


def test_persisted_pipeline_records_supervisor_decision_events(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    pipeline = import_module("synapse_os.pipeline")
    supervisor = import_module("synapse_os.supervisor")

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
            "QUALITY_GATE": _FixedExecutor("quality_gate_md", "# QualityGate\n"),
            "REVIEW": _FixedExecutor("review_md", "# Review\n"),
            "SECURITY": _FixedExecutor("security_md", "# Security\n"),
        },
        supervisor=supervisor.Supervisor(max_retries=2),
    )

    context = runner.run(spec_path, stop_at="SECURITY")
    events = repository.list_events(context.run_id)

    assert [event.event_type for event in events] == [
        "security_provenance_recorded",
        "run_context_initialized",
        "run_started",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
        "supervisor_decision",
        "step_completed",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
        "step_completed",
        "run_completed",
    ]
    assert events[13].state == "CODE_GREEN"
    assert events[14].state == "CODE_GREEN"
    assert "retry" in events[14].message


def test_persisted_pipeline_generates_run_report_until_document(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")

    class _FixedExecutor:
        def __init__(
            self,
            artifact_name: str,
            content: str,
            *,
            tool_name: str | None = None,
        ) -> None:
            self.artifact_name = artifact_name
            self.content = content
            self.tool_name = tool_name

        def execute(self, step, context):  # type: ignore[no-untyped-def]
            del step, context
            pipeline = import_module("synapse_os.pipeline")
            return pipeline.StepExecutionResult(
                artifacts={self.artifact_name: self.content},
                raw_output=self.content,
                clean_output=self.content,
                tool_name=self.tool_name,
                return_code=0 if self.tool_name is not None else None,
                duration_ms=45 if self.tool_name is not None else None,
                timed_out=False if self.tool_name is not None else None,
            )

    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={
            "PLAN": _FixedExecutor("plan_md", "# Plan\n", tool_name="codex"),
            "TEST_RED": _FixedExecutor("tests_md", "# Tests\n"),
            "CODE_GREEN": _FixedExecutor("code_md", "# Green\n"),
            "QUALITY_GATE": _FixedExecutor("quality_gate_md", "# QualityGate\n"),
            "REVIEW": _FixedExecutor("review_md", "# Review\n"),
            "SECURITY": _FixedExecutor("security_md", "# Security\n"),
        },
    )

    context = runner.run(spec_path, stop_at="DOCUMENT")
    run_report_path = artifact_store.base_path / context.run_id / "RUN_REPORT.md"
    run_report_content = run_report_path.read_text(encoding="utf-8")
    steps = repository.list_steps(context.run_id)

    assert context.current_state == "DOCUMENT"
    assert run_report_path.exists()
    assert "# RUN_REPORT" in run_report_content
    assert "codex" in run_report_content
    assert "PLAN" in run_report_content
    assert steps[-1].state == "DOCUMENT"
    assert steps[1].tool_name == "codex"


def test_persisted_pipeline_blocks_unsafe_python_artifact_promotion(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    parsing = import_module("synapse_os.parsing")
    pipeline = import_module("synapse_os.pipeline")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")

    class _UnsafeCodeExecutor:
        def execute(self, step, context):  # type: ignore[no-untyped-def]
            del step, context
            return pipeline.StepExecutionResult(
                artifacts={"code_py": 'eval("danger")\n'},
                raw_output="RAW CODE\n",
                clean_output="eval('danger')\n",
            )

    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={"PLAN": _UnsafeCodeExecutor()},
    )

    with pytest.raises(parsing.ParsingArtifactError, match="unsafe"):
        runner.run(spec_path, stop_at="PLAN")

    runs = repository.list_runs()
    assert len(runs) == 1
    run_record = runs[0]
    events = repository.list_events(run_record.run_id)
    step_directory = artifact_store.base_path / run_record.run_id / "PLAN"
    assert run_record.status == "failed"
    assert run_record.current_state == "PLAN"
    assert not (step_directory / "raw.txt").exists()
    assert not (step_directory / "clean.txt").exists()
    assert not (step_directory / "code_py.txt").exists()
    artifact_paths = artifact_store.list_artifact_paths(run_record.run_id)
    plan_prefix = f"{run_record.run_id}/PLAN/"
    assert all(plan_prefix not in artifact_path for artifact_path in artifact_paths)
    assert [event.event_type for event in events] == [
        "security_provenance_recorded",
        "run_context_initialized",
        "run_started",
        "state_transitioned",
        "step_started",
        "step_completed",
        "state_transitioned",
        "step_started",
        "security_guardrail_triggered",
        "run_failed",
    ]


def test_persisted_pipeline_promotes_safe_python_artifact(tmp_path: Path) -> None:
    persistence = import_module("synapse_os.persistence")
    pipeline = import_module("synapse_os.pipeline")

    spec_path = tmp_path / "SPEC.md"
    _write_valid_spec(spec_path)
    repository = persistence.RunRepository(tmp_path / "runs.sqlite3")
    artifact_store = persistence.ArtifactStore(tmp_path / "artifacts")

    class _SafeCodeExecutor:
        def execute(self, step, context):  # type: ignore[no-untyped-def]
            del step, context
            return pipeline.StepExecutionResult(
                artifacts={"code_py": 'import subprocess as sp\nsp.run(["python", "--version"])\n'},
                raw_output="RAW CODE\n",
                clean_output="safe code\n",
            )

    runner = persistence.PersistedPipelineRunner(
        repository=repository,
        artifact_store=artifact_store,
        executors={"PLAN": _SafeCodeExecutor()},
    )

    context = runner.run(spec_path, stop_at="PLAN")

    artifact_path = artifact_store.base_path / context.run_id / "PLAN" / "code_py.txt"
    assert artifact_path.exists()
    assert "sp.run" in artifact_path.read_text(encoding="utf-8")
