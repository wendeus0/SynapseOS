from unittest.mock import MagicMock

from aignt_os.cli.dashboard import LogViewer


def test_log_viewer_refreshes_file_when_size_changes(tmp_path, monkeypatch):
    log_file = tmp_path / "viewer.log"
    log_file.write_text("line1\nline2\nline3\n", encoding="utf-8")
    monkeypatch.setenv("AIGNT_OS_TUI_LOG_BUFFER_LINES", "2")

    viewer = LogViewer("Test Log", "Initial", path=str(log_file))
    log_widget = MagicMock()
    viewer.query_one = MagicMock(return_value=log_widget)

    viewer.refresh_log()

    log_widget.clear.assert_called_once()
    log_widget.write.assert_called_once_with("\n... 1 lines truncated ...\nline2\nline3\n")

    log_widget.reset_mock()
    viewer.refresh_log()

    log_widget.clear.assert_not_called()
    log_widget.write.assert_not_called()


def test_log_viewer_refresh_ignores_missing_file():
    viewer = LogViewer("Test Log", "Initial", path="/tmp/does-not-exist.log")
    log_widget = MagicMock()
    viewer.query_one = MagicMock(return_value=log_widget)

    viewer.refresh_log()

    log_widget.clear.assert_not_called()
    log_widget.write.assert_not_called()
