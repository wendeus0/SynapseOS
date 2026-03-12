from __future__ import annotations

from io import StringIO

from rich.console import Console

from aignt_os.persistence import RunEventRecord, RunRecord, RunStepRecord


def test_render_run_detail_is_legible_without_tty() -> None:
    cli_rendering = __import__("aignt_os.cli.rendering", fromlist=["render_run_detail"])
    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None, width=160)

    cli_rendering.render_run_detail(
        RunRecord(
            run_id="run-123",
            spec_path="SPEC.md",
            stop_at="DOCUMENT",
            status="completed",
            current_state="DOCUMENT",
            locked=False,
            failure_message=None,
            created_at="2026-03-12T00:00:00+00:00",
            updated_at="2026-03-12T00:01:00+00:00",
            completed_at="2026-03-12T00:02:00+00:00",
        ),
        steps=[
            RunStepRecord(
                step_id=1,
                run_id="run-123",
                state="PLAN",
                status="completed",
                raw_output_path="run-123/PLAN/raw.txt",
                clean_output_path="run-123/PLAN/clean.txt",
                tool_name="codex",
                return_code=0,
                duration_ms=45,
                timed_out=False,
                created_at="2026-03-12T00:00:10+00:00",
            )
        ],
        events=[
            RunEventRecord(
                event_id=1,
                run_id="run-123",
                state="PLAN",
                event_type="step_completed",
                message="Step PLAN completed.",
                created_at="2026-03-12T00:00:11+00:00",
            )
        ],
        artifact_paths=["run-123/PLAN/plan_md.txt", "run-123/RUN_REPORT.md"],
        console=console,
    )

    rendered = output.getvalue()
    assert "Run Detail" in rendered
    assert "Diagnostic Summary" in rendered
    assert "run-123" in rendered
    assert "Latest Signal" in rendered
    assert "step_completed @ PLAN" in rendered
    assert "Latest Timestamp" in rendered
    assert "Next Action" in rendered
    assert "Inspect generated artifacts or report" in rendered
    assert "PLAN" in rendered
    assert "run-123/PLAN/raw.txt" in rendered
    assert "run-123/PLAN/clean.txt" in rendered
    assert "step_completed" in rendered
    assert "2026-03-12T00:00:11+00:00" in rendered
    assert "RUN_REPORT.md" in rendered


def test_render_run_detail_completed_at_spec_validation_guides_canonical_happy_path() -> None:
    cli_rendering = __import__("aignt_os.cli.rendering", fromlist=["render_run_detail"])
    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None, width=160)

    cli_rendering.render_run_detail(
        RunRecord(
            run_id="run-spec-validation",
            spec_path="SPEC.md",
            stop_at="SPEC_VALIDATION",
            status="completed",
            current_state="SPEC_VALIDATION",
            locked=False,
            failure_message=None,
            created_at="2026-03-12T00:00:00+00:00",
            updated_at="2026-03-12T00:01:00+00:00",
            completed_at="2026-03-12T00:02:00+00:00",
        ),
        steps=[],
        events=[],
        artifact_paths=[],
        console=console,
    )

    rendered = output.getvalue()
    assert "SPEC_VALIDATION" in rendered
    assert "Canonical happy path is complete" in rendered
    assert "runs show" not in rendered.lower()
