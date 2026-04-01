from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class TimelineEntry(BaseModel):
    model_config = ConfigDict(strict=True)

    state: str
    entered_at: float
    duration_ms: int


class ExecutionTimeline(BaseModel):
    model_config = ConfigDict(strict=True)

    entries: list[TimelineEntry] = Field(default_factory=list)


class AdapterMetrics(BaseModel):
    model_config = ConfigDict(strict=True)

    tool_name: str
    total_calls: int
    success_count: int
    failure_count: int
    avg_duration_ms: float


class StructuredError(BaseModel):
    model_config = ConfigDict(strict=True)

    error_type: str
    message: str
    step: str
    count: int


class _RunRecordProtocol(Protocol):
    initiated_by: str
    workspace_path: str
    spec_hash: str | None
    status: str
    current_state: str


class _RunStepRecordProtocol(Protocol):
    state: str
    status: str
    tool_name: str | None
    return_code: int | None
    duration_ms: int | None
    timed_out: bool | None


class _RunEventRecordProtocol(Protocol):
    event_type: str
    state: str
    message: str


class _RepositoryProtocol(Protocol):
    def get_run(self, run_id: str) -> _RunRecordProtocol: ...

    def list_steps(self, run_id: str) -> Sequence[_RunStepRecordProtocol]: ...

    def list_events(self, run_id: str) -> Sequence[_RunEventRecordProtocol]: ...


class _ArtifactStoreProtocol(Protocol):
    base_path: Path

    def list_artifact_paths(self, run_id: str) -> list[str]: ...


class RunReport(BaseModel):
    model_config = ConfigDict(strict=True)

    run_id: str
    initiated_by: str
    workspace_path: str
    status: str
    current_state: str
    spec_hash: str | None = None
    feature_id: str | None = None
    feature_title: str | None = None
    execution_timeline: ExecutionTimeline | None = None
    adapter_metrics: list[AdapterMetrics] = Field(default_factory=list)
    structured_errors: list[StructuredError] = Field(default_factory=list)


class RunReportGenerator:
    def __init__(
        self,
        *,
        repository: _RepositoryProtocol,
        artifact_store: _ArtifactStoreProtocol,
    ) -> None:
        self.repository = repository
        self.artifact_store = artifact_store

    def build(self, run_id: str) -> str:
        run_record = self.repository.get_run(run_id)
        step_records = self.repository.list_steps(run_id)
        event_records = self.repository.list_events(run_id)
        spec_id = self._read_spec_artifact(run_id, "spec_id")
        spec_summary = self._read_spec_artifact(run_id, "spec_summary")
        artifact_paths = self.artifact_store.list_artifact_paths(run_id)

        lines = [
            f"# RUN_REPORT — {run_id}",
            "",
            "## Resumo da run",
            "",
            f"- **Status**: {run_record.status}",
            f"- **Estado final**: {run_record.current_state}",
            f"- **Initiated By**: {run_record.initiated_by}",
            f"- **Workspace Path**: {run_record.workspace_path}",
            f"- **Spec Hash**: {run_record.spec_hash or '-'}",
            f"- **SPEC ID**: {spec_id}",
            f"- **SPEC Summary**: {spec_summary}",
            "",
            "## Estados percorridos",
            "",
            "| Estado | Status | Ferramenta | Return code | Duração (ms) | Timeout |",
            "|---|---|---|---|---|---|",
        ]

        for step_record in step_records:
            lines.append(
                "| "
                f"{step_record.state} | "
                f"{step_record.status} | "
                f"{step_record.tool_name or '-'} | "
                f"{self._format_optional(step_record.return_code)} | "
                f"{self._format_optional(step_record.duration_ms)} | "
                f"{self._format_timeout(step_record.timed_out)} |"
            )

        lines.extend(
            [
                "",
                "## Eventos relevantes",
                "",
            ]
        )

        for event_record in event_records:
            lines.append(
                f"- `{event_record.event_type}` @ `{event_record.state}`: {event_record.message}"
            )

        failure_events = [
            event_record
            for event_record in event_records
            if event_record.event_type in {"run_failed", "supervisor_decision"}
        ]
        lines.extend(
            [
                "",
                "## Falhas e retries",
                "",
            ]
        )
        if failure_events:
            for event_record in failure_events:
                lines.append(
                    f"- `{event_record.event_type}` @ "
                    f"`{event_record.state}`: {event_record.message}"
                )
        else:
            lines.append("Nenhuma falha registrada nesta execução.")

        lines.extend(
            [
                "",
                "## Artefatos gerados",
                "",
            ]
        )
        for artifact_path in artifact_paths:
            if artifact_path.endswith("RUN_REPORT.md"):
                continue
            lines.append(f"- `artifacts/{artifact_path}`")

        return "\n".join(lines) + "\n"

    def _read_spec_artifact(self, run_id: str, artifact_name: str) -> str:
        artifact_path = (
            self.artifact_store.base_path
            / run_id
            / "SPEC_VALIDATION"
            / f"{artifact_name}.txt"
        )
        if not artifact_path.exists():
            return "-"
        return artifact_path.read_text(encoding="utf-8").strip() or "-"

    def _format_optional(self, value: int | None) -> str:
        if value is None:
            return "-"
        return str(value)

    def _format_timeout(self, value: bool | None) -> str:
        if value is None:
            return "-"
        return "yes" if value else "no"

    def generate_structured_report(self, run_id: str) -> RunReport:
        run_record = self.repository.get_run(run_id)
        step_records = self.repository.list_steps(run_id)
        event_records = self.repository.list_events(run_id)
        spec_id = self._read_spec_artifact(run_id, "spec_id")
        spec_title = self._read_spec_artifact(run_id, "spec_title")

        timeline_entries: list[TimelineEntry] = []
        previous_entered_at: float | None = None
        adapter_call_counts: dict[str, dict[str, int | float]] = {}

        for event in event_records:
            if event.event_type == "state_entered" and event.state:
                entered_at = getattr(event, "timestamp", None)
                if entered_at is None:
                    entered_at = 0.0
                duration_ms = 0
                if previous_entered_at is not None:
                    duration_ms = int((entered_at - previous_entered_at) * 1000)
                timeline_entries.append(
                    TimelineEntry(
                        state=event.state,
                        entered_at=entered_at,
                        duration_ms=duration_ms,
                    )
                )
                previous_entered_at = entered_at

        for step in step_records:
            tool = step.tool_name or "unknown"
            if tool not in adapter_call_counts:
                adapter_call_counts[tool] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "duration_sum": 0,
                }
            adapter_call_counts[tool]["total"] += 1
            if step.return_code == 0:
                adapter_call_counts[tool]["success"] += 1
            else:
                adapter_call_counts[tool]["failure"] += 1
            if step.duration_ms is not None:
                adapter_call_counts[tool]["duration_sum"] += step.duration_ms

        adapter_metrics: list[AdapterMetrics] = []
        for tool_name, counts in adapter_call_counts.items():
            total = counts["total"]
            avg = counts["duration_sum"] / total if total > 0 else 0.0
            adapter_metrics.append(
                AdapterMetrics(
                    tool_name=tool_name,
                    total_calls=int(total),
                    success_count=int(counts["success"]),
                    failure_count=int(counts["failure"]),
                    avg_duration_ms=avg,
                )
            )

        return RunReport(
            run_id=run_id,
            initiated_by=run_record.initiated_by,
            workspace_path=run_record.workspace_path,
            status=run_record.status,
            current_state=run_record.current_state,
            spec_hash=run_record.spec_hash,
            feature_id=spec_id if spec_id != "-" else None,
            feature_title=spec_title if spec_title != "-" else None,
            execution_timeline=(
                ExecutionTimeline(entries=timeline_entries)
                if timeline_entries
                else None
            ),
            adapter_metrics=adapter_metrics,
            structured_errors=[],
        )
