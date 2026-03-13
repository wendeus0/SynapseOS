from unittest.mock import MagicMock, patch

from aignt_os.cli.dashboard import LogViewer, RunDashboard
from aignt_os.persistence import RunStepRecord

MOCK_STEP = RunStepRecord(
    step_id=1,
    run_id="test-run",
    tool_name="test-tool",
    status="completed",
    state="success",
    raw_output_path="/tmp/mock.log",
    clean_output_path=None,
    return_code=0,
    duration_ms=100,
    timed_out=False,
    created_at="2023-01-01T00:00:00",
)


def test_action_show_logs_reads_file_and_pushes_screen():
    """Verify the logic of action_show_logs without running the full TUI loop."""
    app = RunDashboard(run_id="test-run")

    # Manually setup state
    # We must mock query_one or set up the widget structure because setting .step triggers a watcher
    # which calls query_one.
    app.step_detail.query_one = MagicMock()
    app.step_detail.step = MOCK_STEP
    app.push_screen = MagicMock()
    app.notify = MagicMock()

    # Mock pathlib.Path to simulate file existence and content
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="Mock Log Content"),
    ):
        app.action_show_logs()

    # Verification
    app.push_screen.assert_called_once()
    call_args = app.push_screen.call_args[0]
    assert isinstance(call_args[0], LogViewer)
    assert call_args[0].log_content == "Mock Log Content"


def test_action_show_logs_handles_missing_file():
    """Verify graceful handling when log file is missing."""
    app = RunDashboard(run_id="test-run")
    app.step_detail.query_one = MagicMock()
    app.step_detail.step = MOCK_STEP
    app.push_screen = MagicMock()

    with patch("pathlib.Path.exists", return_value=False):
        app.action_show_logs()

    app.push_screen.assert_called_once()
    call_args = app.push_screen.call_args[0]
    # Should still show modal, but with "No logs available" (or error msg if exception)
    # Our implementation sets "No logs available." initially
    assert isinstance(call_args[0], LogViewer)
    assert call_args[0].log_content == "No logs available."


def test_action_show_logs_warns_if_no_step_selected():
    app = RunDashboard(run_id="test-run")
    app.step_detail.query_one = MagicMock()
    app.step_detail.step = None
    app.push_screen = MagicMock()
    app.notify = MagicMock()

    app.action_show_logs()

    app.push_screen.assert_not_called()
    app.notify.assert_called_once_with("Select a step first.", severity="warning")
