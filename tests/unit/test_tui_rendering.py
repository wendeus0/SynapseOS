from aignt_os.cli.rendering import truncate_logs


def test_truncate_logs_empty():
    assert truncate_logs("", 10) == ""
    assert truncate_logs(None, 10) == ""


def test_truncate_logs_below_limit():
    text = "line1\nline2\nline3"
    assert truncate_logs(text, 10) == text


def test_truncate_logs_at_limit():
    text = "line1\nline2\nline3"
    assert truncate_logs(text, 3) == text


def test_truncate_logs_exceeds_limit():
    text = "line1\nline2\nline3\nline4\nline5"
    truncated = truncate_logs(text, 2)

    assert "truncated" in truncated
    assert "3 lines truncated" in truncated
    assert truncated.endswith("line4\nline5")
    assert "line1" not in truncated


def test_truncate_logs_single_line_limit():
    text = "line1\nline2\nline3"
    truncated = truncate_logs(text, 1)

    assert "truncated" in truncated
    assert truncated.endswith("line3")
