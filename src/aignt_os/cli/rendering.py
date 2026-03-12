from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from aignt_os.runtime.state import RuntimeState


def render_runtime_status(
    state: RuntimeState,
    *,
    console: Console | None = None,
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

    output_console.print(
        Panel.fit(
            Group(*lines),
            border_style=status_style,
            padding=(0, 1),
            title="runtime status",
        )
    )


def _status_style(status: str) -> str:
    if status == "running":
        return "green"
    if status == "stopped":
        return "yellow"
    if status == "inconsistent":
        return "red"
    return "cyan"
