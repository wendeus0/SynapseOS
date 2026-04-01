from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestExecutionTimelineModels:
    def test_timeline_entry_model(self) -> None:
        from synapse_os.reporting import TimelineEntry

        entry = TimelineEntry(
            state="CODE_GREEN",
            entered_at=1000.0,
            duration_ms=500,
        )
        assert entry.state == "CODE_GREEN"
        assert entry.entered_at == 1000.0
        assert entry.duration_ms == 500

    def test_execution_timeline_model(self) -> None:
        from synapse_os.reporting import ExecutionTimeline, TimelineEntry

        entry = TimelineEntry(state="PLAN", entered_at=0.0, duration_ms=100)
        timeline = ExecutionTimeline(entries=[entry])
        assert len(timeline.entries) == 1
        assert timeline.entries[0].state == "PLAN"


class TestAdapterMetricsModel:
    def test_adapter_metrics_model(self) -> None:
        from synapse_os.reporting import AdapterMetrics

        metrics = AdapterMetrics(
            tool_name="codex",
            total_calls=10,
            success_count=8,
            failure_count=2,
            avg_duration_ms=1500.5,
        )
        assert metrics.tool_name == "codex"
        assert metrics.total_calls == 10
        assert metrics.success_count == 8
        assert metrics.failure_count == 2
        assert metrics.avg_duration_ms == 1500.5


class TestStructuredErrorModel:
    def test_structured_error_model(self) -> None:
        from synapse_os.reporting import StructuredError

        error = StructuredError(
            error_type="RetryableStepError",
            message="temporary failure",
            step="CODE_GREEN",
            count=2,
        )
        assert error.error_type == "RetryableStepError"
        assert error.message == "temporary failure"
        assert error.step == "CODE_GREEN"
        assert error.count == 2


class TestRunReportEnhancedFields:
    def test_run_report_has_feature_id_and_title(self) -> None:
        from synapse_os.reporting import RunReport

        report = RunReport(
            run_id="test-run",
            initiated_by="agent",
            workspace_path="/workspace",
            status="completed",
            current_state="DONE",
            feature_id="F64-advanced-supervisor-policies",
            feature_title="Advanced Supervisor Policies",
        )
        assert report.feature_id == "F64-advanced-supervisor-policies"
        assert report.feature_title == "Advanced Supervisor Policies"

    def test_run_report_has_execution_timeline(self) -> None:
        from synapse_os.reporting import ExecutionTimeline, RunReport, TimelineEntry

        timeline = ExecutionTimeline(
            entries=[
                TimelineEntry(state="PLAN", entered_at=0.0, duration_ms=100),
                TimelineEntry(state="CODE_GREEN", entered_at=0.1, duration_ms=200),
            ]
        )
        report = RunReport(
            run_id="test-run",
            initiated_by="agent",
            workspace_path="/workspace",
            status="completed",
            current_state="DONE",
            execution_timeline=timeline,
        )
        assert len(report.execution_timeline.entries) == 2

    def test_run_report_has_adapter_metrics(self) -> None:
        from synapse_os.reporting import AdapterMetrics, RunReport

        metrics = [
            AdapterMetrics(
                tool_name="codex",
                total_calls=5,
                success_count=4,
                failure_count=1,
                avg_duration_ms=1000.0,
            ),
        ]
        report = RunReport(
            run_id="test-run",
            initiated_by="agent",
            workspace_path="/workspace",
            status="completed",
            current_state="DONE",
            adapter_metrics=metrics,
        )
        assert len(report.adapter_metrics) == 1
        assert report.adapter_metrics[0].tool_name == "codex"

    def test_run_report_has_structured_errors(self) -> None:
        from synapse_os.reporting import RunReport, StructuredError

        errors = [
            StructuredError(
                error_type="RetryableStepError",
                message="failure",
                step="CODE_GREEN",
                count=3,
            ),
        ]
        report = RunReport(
            run_id="test-run",
            initiated_by="agent",
            workspace_path="/workspace",
            status="failed",
            current_state="CODE_GREEN",
            structured_errors=errors,
        )
        assert len(report.structured_errors) == 1
        assert report.structured_errors[0].count == 3


class TestGenerateStructuredReport:
    def test_generate_structured_report_populates_timeline(self) -> None:
        import tempfile
        from pathlib import Path

        from synapse_os.reporting import RunReportGenerator

        run_record = MagicMock()
        run_record.initiated_by = "agent"
        run_record.workspace_path = "/workspace"
        run_record.spec_hash = "abc123"
        run_record.status = "completed"
        run_record.current_state = "DONE"

        step_records = [
            MagicMock(
                state="PLAN",
                status="done",
                tool_name="codex",
                return_code=0,
                duration_ms=100,
                timed_out=False,
            ),
            MagicMock(
                state="TEST_RED",
                status="done",
                tool_name="codex",
                return_code=0,
                duration_ms=200,
                timed_out=False,
            ),
        ]

        event_records = [
            MagicMock(
                event_type="state_entered",
                state="PLAN",
                message="entered PLAN",
                timestamp=1000.0,
            ),
            MagicMock(
                event_type="state_entered",
                state="TEST_RED",
                message="entered TEST_RED",
                timestamp=1100.0,
            ),
        ]

        repo = MagicMock()
        repo.get_run.return_value = run_record
        repo.list_steps.return_value = step_records
        repo.list_events.return_value = event_records

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            spec_id_file = base / "test-run" / "SPEC_VALIDATION" / "spec_id.txt"
            spec_id_file.parent.mkdir(parents=True)
            spec_id_file.write_text("F64-advanced-supervisor-policies")

            artifact_store = MagicMock()
            artifact_store.base_path = base
            artifact_store.list_artifact_paths.return_value = []

            gen = RunReportGenerator(repository=repo, artifact_store=artifact_store)
            structured = gen.generate_structured_report("test-run")
            assert structured.feature_id == "F64-advanced-supervisor-policies"
            assert len(structured.execution_timeline.entries) == 2
        assert len(structured.execution_timeline.entries) == 2

    def test_generate_structured_report_aggregates_adapter_metrics(self) -> None:
        from pathlib import Path

        from synapse_os.reporting import RunReportGenerator

        run_record = MagicMock()
        run_record.initiated_by = "agent"
        run_record.workspace_path = "/workspace"
        run_record.spec_hash = "hash"
        run_record.status = "failed"
        run_record.current_state = "CODE_GREEN"

        step_records = [
            MagicMock(
                state="PLAN",
                status="done",
                tool_name="codex",
                return_code=0,
                duration_ms=100,
                timed_out=False,
            ),
            MagicMock(
                state="TEST_RED",
                status="done",
                tool_name="codex",
                return_code=0,
                duration_ms=200,
                timed_out=False,
            ),
            MagicMock(
                state="CODE_GREEN",
                status="failed",
                tool_name="gemini",
                return_code=1,
                duration_ms=300,
                timed_out=False,
            ),
        ]

        event_records = []

        repo = MagicMock()
        repo.get_run.return_value = run_record
        repo.list_steps.return_value = step_records
        repo.list_events.return_value = event_records

        artifact_store = MagicMock()
        artifact_store.base_path = Path("/tmp/fake")
        artifact_store.list_artifact_paths.return_value = []

        gen = RunReportGenerator(repository=repo, artifact_store=artifact_store)
        structured = gen.generate_structured_report("test-run")

        codex_metrics = next(
            (m for m in structured.adapter_metrics if m.tool_name == "codex"), None
        )
        gemini_metrics = next(
            (m for m in structured.adapter_metrics if m.tool_name == "gemini"), None
        )
        assert codex_metrics is not None
        assert codex_metrics.total_calls == 2
        assert codex_metrics.success_count == 2
        assert gemini_metrics is not None
        assert gemini_metrics.total_calls == 1
        assert gemini_metrics.failure_count == 1
