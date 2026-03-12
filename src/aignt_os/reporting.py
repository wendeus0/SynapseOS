from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol


class _RunRecordProtocol(Protocol):
    initiated_by: str
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
            self.artifact_store.base_path / run_id / "SPEC_VALIDATION" / f"{artifact_name}.txt"
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
