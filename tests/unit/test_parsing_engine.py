from importlib import import_module
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "cli_outputs"


def _parsing_module():
    return import_module("aignt_os.parsing")


def _read_fixture(name: str, *, unicode_escape: bool = False) -> str:
    text = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    if unicode_escape:
        return text.encode("utf-8").decode("unicode_escape")
    return text


def test_parse_cli_output_keeps_raw_and_removes_ansi_sequences() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("noisy_mixed_output.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.stdout_raw == raw_output
    assert "\u001b[" not in parsed_output.stdout_clean
    assert "INFO Build summary follows" in parsed_output.stdout_clean
    assert "[transport] adapter heartbeat" not in parsed_output.stdout_clean
    assert "def greet" in parsed_output.stdout_clean


def test_parse_cli_output_extracts_python_fenced_block() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("noisy_mixed_output.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert len(parsed_output.artifacts) == 1
    assert parsed_output.artifacts[0].language == "python"
    assert "def greet" in parsed_output.artifacts[0].content


def test_parse_cli_output_normalizes_capitalized_python_language() -> None:
    parsing = _parsing_module()
    raw_output = """```Python
def greet() -> str:
    return "hello"
```"""

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.artifacts[0].language == "python"


def test_validate_python_artifact_accepts_valid_python_code() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("noisy_mixed_output.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    parsing.validate_python_artifact(parsed_output.artifacts[0])


def test_validate_python_artifact_accepts_py_alias() -> None:
    parsing = _parsing_module()
    raw_output = """```py
def greet() -> str:
    return "hello"
```"""
    parsed_output = parsing.parse_cli_output(raw_output)

    parsing.validate_python_artifact(parsed_output.artifacts[0])


def test_validate_python_artifact_rejects_corrupted_python_code() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("invalid_python_block.txt")
    parsed_output = parsing.parse_cli_output(raw_output)

    with pytest.raises(parsing.ParsingArtifactError, match="Python"):
        parsing.validate_python_artifact(parsed_output.artifacts[0])


def test_parse_cli_output_rejects_raw_output_larger_than_mvp_limit() -> None:
    parsing = _parsing_module()
    raw_output = "x" * (1024 * 1024 + 1)

    with pytest.raises(parsing.ParsingArtifactError, match="too large"):
        parsing.parse_cli_output(raw_output)


def test_parse_cli_output_rejects_more_than_32_artifacts() -> None:
    parsing = _parsing_module()
    raw_output = "\n".join(f"```python\nprint({index})\n```" for index in range(33))

    with pytest.raises(parsing.ParsingArtifactError, match="Too many"):
        parsing.parse_cli_output(raw_output)


def test_parse_cli_output_rejects_oversized_artifact() -> None:
    parsing = _parsing_module()
    large_content = "x" * (128 * 1024 + 1)
    raw_output = f"```python\n{large_content}\n```"

    with pytest.raises(parsing.ParsingArtifactError, match="Artifact"):
        parsing.parse_cli_output(raw_output)
