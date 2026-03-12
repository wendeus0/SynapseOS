from __future__ import annotations

from io import StringIO

from rich.console import Console

from aignt_os.runtime.state import RuntimeState


def test_render_runtime_status_is_legible_without_tty() -> None:
    cli_rendering = __import__("aignt_os.cli.rendering", fromlist=["render_runtime_status"])
    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None, width=80)

    cli_rendering.render_runtime_status(
        RuntimeState(status="running", pid=4321),
        console=console,
    )

    rendered = output.getvalue()
    assert "AIgnt OS Runtime" in rendered
    assert "Status" in rendered
    assert "running" in rendered.lower()
    assert "PID" in rendered
    assert "4321" in rendered
