from __future__ import annotations

from io import StringIO

from rich.console import Console


def test_render_environment_doctor_is_legible_without_tty() -> None:
    cli_rendering = __import__("aignt_os.cli.rendering", fromlist=["render_environment_doctor"])
    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None, width=120)

    cli_rendering.render_environment_doctor(
        overall_status="pass",
        checks=[
            {
                "name": "runtime_state",
                "status": "warn",
                "target": ".aignt-os/runtime/runtime-state.json",
                "message": "Runtime is stopped but the sync happy path remains available.",
                "next_step": "Start the runtime only if you need async dispatch.",
            },
            {
                "name": "runs_db",
                "status": "pass",
                "target": ".aignt-os/runs/runs.sqlite3",
                "message": "Run persistence path is writable.",
                "next_step": "You can submit a run with `aignt runs submit`.",
            },
            {
                "name": "artifacts_dir",
                "status": "pass",
                "target": ".aignt-os/artifacts",
                "message": "Artifacts directory is writable.",
                "next_step": "Inspect persisted outputs with `aignt runs show <run_id>`.",
            },
        ],
        console=console,
    )

    rendered = output.getvalue()
    assert "Environment Doctor" in rendered
    assert "Overall Status" in rendered
    assert "pass" in rendered.lower()
    assert "runtime_state" in rendered
    assert "runs_db" in rendered
    assert "artifacts_dir" in rendered
    assert "warn" in rendered.lower()
    assert "Start the runtime only if you need async dispatch." in rendered
    assert "You can submit a run with `aignt runs submit`." in rendered


def test_render_environment_doctor_surfaces_blocking_failures() -> None:
    cli_rendering = __import__("aignt_os.cli.rendering", fromlist=["render_environment_doctor"])
    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None, width=120)

    cli_rendering.render_environment_doctor(
        overall_status="fail",
        checks=[
            {
                "name": "runs_db",
                "status": "fail",
                "target": "/tmp/not-a-dir/runs.sqlite3",
                "message": "Parent directory is not writable for the current process.",
                "next_step": "Fix the configured path or permissions before submitting a run.",
            }
        ],
        console=console,
    )

    rendered = output.getvalue()
    assert "Environment Doctor" in rendered
    assert "Overall Status" in rendered
    assert "fail" in rendered.lower()
    assert "runs_db" in rendered
    assert "/tmp/not-a-dir/runs.sqlite3" in rendered
    assert "Fix the configured path or permissions before submitting a run." in rendered
