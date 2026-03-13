from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from rich.console import Console, ConsoleRenderable, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aignt_os.persistence import RunEventRecord, RunRecord, RunStepRecord
from aignt_os.runtime.dispatch import RunDispatchResult
from aignt_os.runtime.state import RuntimeState


@dataclass(frozen=True, slots=True)
class RunArtifactPreview:
    target: str
    source_path: str
    content: str
    truncated: bool


def truncate_logs(text: str | None, max_lines: int) -> str:
    if not text:
        return ""

    lines = text.splitlines(keepends=True)
    if len(lines) <= max_lines:
        return text

    truncated_count = len(lines) - max_lines
    kept_lines = lines[-max_lines:]
    marker = f"\n... {truncated_count} lines truncated ...\n"
    return marker + "".join(kept_lines)


def render_runtime_status(
    state: RuntimeState,
    *,
    console: Console | None = None,
    show_started_by: bool = False,
) -> None:
    output_console = console or Console()
    status_style = _status_style(state.status)

    lines: list[Text] = [
        Text("AIgnt OS Runtime", style="bold cyan"),
        Text.assemble(("Status: ", "dim"), (state.status, status_style)),
    ]
    if state.pid is not None:
        lines.append(Text.assemble(("PID: ", "dim"), (str(state.pid), "bold")))

    if state.started_at:
        lines.append(Text.assemble(("Started at: ", "dim"), state.started_at))
    if show_started_by:
        started_by_value = state.started_by or "unavailable"
        lines.append(Text.assemble(("Started by: ", "dim"), started_by_value))

    output_console.print(
        Panel.fit(
            Group(*lines),
            border_style=status_style,
            padding=(0, 1),
            title="runtime status",
        )
    )


def render_runs_list(
    runs: Sequence[RunRecord],
    *,
    console: Console | None = None,
) -> None:
    output_console = console or Console(width=160)
    if not runs:
        output_console.print(
            Panel.fit(
                "No runs found.",
                border_style="yellow",
                padding=(0, 1),
                title="runs",
            )
        )
        return

    table = Table(title="Persisted Runs")
    table.add_column("Run ID", style="bold")
    table.add_column("Status")
    table.add_column("Current State")
    table.add_column("Stop At")
    table.add_column("Updated At")

    for run in runs:
        table.add_row(
            run.run_id,
            Text(run.status, style=_status_style(run.status)),
            run.current_state,
            run.stop_at,
            run.updated_at,
        )

    output_console.print(table)


def render_run_detail(
    run: RunRecord,
    *,
    steps: Sequence[RunStepRecord],
    events: Sequence[RunEventRecord],
    artifact_paths: Sequence[str],
    preview: RunArtifactPreview | None = None,
    console: Console | None = None,
) -> None:
    output_console = console or Console(width=160)
    latest_event = events[-1] if events else None
    summary_table = Table.grid(expand=False)
    summary_table.add_column(style="dim")
    summary_table.add_column()
    summary_table.add_row("Run ID", run.run_id)
    summary_table.add_row("Status", Text(run.status, style=_status_style(run.status)))
    summary_table.add_row("Current State", run.current_state)
    summary_table.add_row("Stop At", run.stop_at)
    summary_table.add_row("Spec Path", run.spec_path)
    summary_table.add_row("Spec Hash", run.spec_hash or "-")
    summary_table.add_row("Initiated By", run.initiated_by)
    summary_table.add_row("Locked", "yes" if run.locked else "no")
    summary_table.add_row("Created At", run.created_at)
    summary_table.add_row("Updated At", run.updated_at)
    if run.completed_at is not None:
        summary_table.add_row("Completed At", run.completed_at)
    if run.failure_message is not None:
        summary_table.add_row("Failure", run.failure_message)

    diagnostic_table = Table.grid(expand=False)
    diagnostic_table.add_column(style="dim")
    diagnostic_table.add_column()
    diagnostic_table.add_row("Status", Text(run.status, style=_status_style(run.status)))
    diagnostic_table.add_row("Current State", run.current_state)
    diagnostic_table.add_row("Latest Signal", _latest_signal(latest_event))
    diagnostic_table.add_row(
        "Latest Timestamp",
        _latest_timestamp(run, latest_event),
    )
    diagnostic_table.add_row("Next Action", _next_action(run))

    renderables: list[ConsoleRenderable] = [
        Panel.fit(
            summary_table,
            border_style=_status_style(run.status),
            padding=(0, 1),
            title="Run Detail",
        ),
        Panel.fit(
            diagnostic_table,
            border_style=_status_style(run.status),
            padding=(0, 1),
            title="Diagnostic Summary",
        ),
    ]
    if preview is not None:
        renderables.append(_artifact_preview_panel(preview))
    renderables.append(_steps_table(steps))
    renderables.append(_events_table(events))
    renderables.append(_artifacts_table(artifact_paths))
    output_console.print(Group(*renderables))


def render_run_submission(
    result: RunDispatchResult,
    *,
    console: Console | None = None,
) -> None:
    output_console = console or Console()
    lines = [
        Text.assemble(("run_id: ", "dim"), result.run_id),
        Text.assemble(
            ("status: ", "dim"),
            (result.status, _status_style(result.status)),
        ),
        Text.assemble(("mode: ", "dim"), result.dispatch_mode_resolved),
    ]

    output_console.print(
        Panel.fit(
            Group(*lines),
            border_style=_status_style(result.status),
            padding=(0, 1),
            title="Run Submission",
        )
    )


def render_environment_doctor(
    *,
    overall_status: str,
    checks: Sequence[Mapping[str, str]],
    console: Console | None = None,
) -> None:
    output_console = console or Console(width=160)
    summary_table = Table.grid(expand=False)
    summary_table.add_column(style="dim")
    summary_table.add_column()
    summary_table.add_row(
        "Overall Status",
        Text(overall_status, style=_status_style(overall_status)),
    )

    check_renderables: list[ConsoleRenderable] = []
    for check in checks:
        check_table = Table.grid(expand=False)
        check_table.add_column(style="dim")
        check_table.add_column()
        check_table.add_row("Check", check["name"])
        check_table.add_row(
            "Status",
            Text(check["status"], style=_status_style(check["status"])),
        )
        check_table.add_row("Target", check["target"])
        check_table.add_row("Message", check["message"])
        check_table.add_row("Next Step", check["next_step"])
        check_renderables.append(
            Panel.fit(
                check_table,
                border_style=_status_style(check["status"]),
                padding=(0, 1),
                title=f"Check: {check['name']}",
            )
        )

    output_console.print(
        Group(
            Panel.fit(
                summary_table,
                border_style=_status_style(overall_status),
                padding=(0, 1),
                title="Environment Doctor",
            ),
            *check_renderables,
        )
    )


def _status_style(status: str) -> str:
    if status == "running":
        return "green"
    if status == "completed":
        return "green"
    if status == "pass":
        return "green"
    if status == "warn":
        return "yellow"
    if status == "failed":
        return "red"
    if status == "fail":
        return "red"
    if status == "stopped":
        return "yellow"
    if status == "inconsistent":
        return "red"
    return "cyan"


def _steps_table(steps: Sequence[RunStepRecord]) -> Table:
    table = Table(title="Steps")
    table.add_column("State", style="bold")
    table.add_column("Status")
    table.add_column("Tool")
    table.add_column("Return Code")
    table.add_column("Duration (ms)")
    table.add_column("Timed Out")
    table.add_column("Raw Output")
    table.add_column("Clean Output")

    if not steps:
        table.add_row("-", "No persisted steps.", "-", "-", "-", "-", "-", "-")
        return table

    for step in steps:
        table.add_row(
            step.state,
            step.status,
            step.tool_name or "-",
            "-" if step.return_code is None else str(step.return_code),
            "-" if step.duration_ms is None else str(step.duration_ms),
            "-" if step.timed_out is None else ("yes" if step.timed_out else "no"),
            step.raw_output_path or "-",
            step.clean_output_path or "-",
        )
    return table


def _events_table(events: Sequence[RunEventRecord]) -> Table:
    table = Table(title="Events")
    table.add_column("State", style="bold")
    table.add_column("Event Type")
    table.add_column("Message")
    table.add_column("Created At")

    if not events:
        table.add_row("-", "No persisted events.", "-", "-")
        return table

    for event in events:
        table.add_row(event.state, event.event_type, event.message, event.created_at)
    return table


def _artifacts_table(artifact_paths: Sequence[str]) -> Table:
    table = Table(title="Artifacts")
    table.add_column("Scope", style="bold")
    table.add_column("Path")

    if not artifact_paths:
        table.add_row("-", "No persisted artifacts.")
        return table

    for artifact_path in artifact_paths:
        table.add_row(_artifact_scope(artifact_path), artifact_path)
    return table


def _artifact_preview_panel(preview: RunArtifactPreview) -> Panel:
    preview_table = Table.grid(expand=False)
    preview_table.add_column(style="dim")
    preview_table.add_column()
    preview_table.add_row("Target", preview.target)
    preview_table.add_row("Source Path", preview.source_path)
    preview_table.add_row("Content", preview.content.rstrip("\n") or "(empty file)")
    if preview.truncated:
        preview_table.add_row("Notice", "Preview truncated after 40 lines.")

    return Panel.fit(
        preview_table,
        border_style="cyan",
        padding=(0, 1),
        title="Artifact Preview",
    )


def _latest_signal(event: RunEventRecord | None) -> str:
    if event is None:
        return "No persisted events yet."
    return f"{event.event_type} @ {event.state}"


def _latest_timestamp(run: RunRecord, event: RunEventRecord | None) -> str:
    if event is not None:
        return event.created_at
    if run.completed_at is not None:
        return run.completed_at
    return run.updated_at


def _next_action(run: RunRecord) -> str:
    if run.status == "failed":
        return "Inspect failure details and latest step outputs."
    if run.status == "pending":
        return "Start the runtime or wait for the worker to pick up this run."
    if run.status == "running":
        return "Monitor the current state and latest event for progress."
    if run.status == "completed" and run.current_state == "SPEC_VALIDATION":
        return "Canonical happy path is complete. Inspect persisted signals for audit."
    if run.status == "completed":
        return "Inspect generated artifacts or report for outputs."
    return "Inspect the latest persisted signals for the next action."


def _artifact_scope(artifact_path: str) -> str:
    parts = artifact_path.split("/")
    if len(parts) < 2:
        return "RUN"
    if parts[-1] == "RUN_REPORT.md":
        return "RUN"
    return parts[1]
