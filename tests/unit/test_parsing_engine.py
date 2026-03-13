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


# ---------------------------------------------------------------------------
# Raw vs clean separation
# ---------------------------------------------------------------------------


def test_parse_cli_output_keeps_raw_and_removes_ansi_sequences() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("noisy_mixed_output.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.stdout_raw == raw_output
    assert "\u001b[" not in parsed_output.stdout_clean
    assert "INFO Build summary follows" in parsed_output.stdout_clean
    assert "[transport] adapter heartbeat" not in parsed_output.stdout_clean
    assert "def greet" in parsed_output.stdout_clean


def test_parse_cli_output_raw_is_preserved_exactly() -> None:
    parsing = _parsing_module()
    raw_output = "\u001b[32mINFO\u001b[0m hello world\n"

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.stdout_raw == raw_output


# ---------------------------------------------------------------------------
# Code block extraction
# ---------------------------------------------------------------------------


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


def test_parse_cli_output_extracts_multiple_python_blocks() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("multiple_python_blocks.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert len(parsed_output.artifacts) == 2
    assert all(a.language == "python" for a in parsed_output.artifacts)
    assert any("def greet" in a.content for a in parsed_output.artifacts)
    assert any("def farewell" in a.content for a in parsed_output.artifacts)


def test_parse_cli_output_produces_no_artifacts_when_no_code_block_present() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("noisy_no_code_block.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.artifacts == []


def test_parse_cli_output_clean_output_strips_transport_noise() -> None:
    parsing = _parsing_module()
    raw_output = _read_fixture("noisy_no_code_block.txt", unicode_escape=True)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert "[transport]" not in parsed_output.stdout_clean


def test_parse_cli_output_normalizes_unicode_and_strips_bidi_controls() -> None:
    parsing = _parsing_module()
    raw_output = "e\u0301 \u202eＦ\n"

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.stdout_clean == "é F"


def test_parse_cli_output_masks_secrets_in_clean_output_but_preserves_artifact_content() -> None:
    parsing = _parsing_module()
    raw_output = """Bearer secret-token
```python
token = "sk-secret123"
```
"""

    parsed_output = parsing.parse_cli_output(raw_output)

    assert "Bearer secret-token" not in parsed_output.stdout_clean
    assert "sk-secret123" not in parsed_output.stdout_clean
    assert "[REDACTED]" in parsed_output.stdout_clean
    assert parsed_output.artifacts[0].content == 'token = "sk-secret123"'


# ---------------------------------------------------------------------------
# Python artifact validation
# ---------------------------------------------------------------------------


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


def test_validate_python_artifact_rejects_eval_calls() -> None:
    parsing = _parsing_module()
    raw_output = """```python
value = eval("1 + 1")
```"""
    parsed_output = parsing.parse_cli_output(raw_output)

    with pytest.raises(parsing.ParsingArtifactError, match="unsafe"):
        parsing.validate_python_artifact(parsed_output.artifacts[0])


def test_validate_python_artifact_rejects_os_system_alias_calls() -> None:
    parsing = _parsing_module()
    raw_output = """```python
import os as platform_os

platform_os.system("echo dangerous")
```"""
    parsed_output = parsing.parse_cli_output(raw_output)

    with pytest.raises(parsing.ParsingArtifactError, match="unsafe"):
        parsing.validate_python_artifact(parsed_output.artifacts[0])


def test_validate_python_artifact_rejects_subprocess_alias_with_shell_true() -> None:
    parsing = _parsing_module()
    raw_output = """```python
from subprocess import run as spawn

spawn("echo dangerous", shell=True)
```"""
    parsed_output = parsing.parse_cli_output(raw_output)

    with pytest.raises(parsing.ParsingArtifactError, match="unsafe"):
        parsing.validate_python_artifact(parsed_output.artifacts[0])


def test_validate_python_artifact_accepts_subprocess_run_without_shell_true() -> None:
    parsing = _parsing_module()
    raw_output = """```python
import subprocess as sp

sp.run(["python", "--version"])
```"""
    parsed_output = parsing.parse_cli_output(raw_output)

    parsing.validate_python_artifact(parsed_output.artifacts[0])


# ---------------------------------------------------------------------------
# Size and count limits
# ---------------------------------------------------------------------------


def test_parse_cli_output_rejects_raw_output_larger_than_mvp_limit() -> None:
    parsing = _parsing_module()
    raw_output = "x" * (1024 * 1024 + 1)

    with pytest.raises(parsing.ParsingArtifactError, match="too large"):
        parsing.parse_cli_output(raw_output)


def test_parse_cli_output_accepts_raw_output_at_exact_mvp_limit() -> None:
    parsing = _parsing_module()
    raw_output = "x" * (1024 * 1024)

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.artifacts == []


def test_parse_cli_output_rejects_more_than_32_artifacts() -> None:
    parsing = _parsing_module()
    raw_output = "\n".join(f"```python\nprint({index})\n```" for index in range(33))

    with pytest.raises(parsing.ParsingArtifactError, match="Too many"):
        parsing.parse_cli_output(raw_output)


def test_parse_cli_output_accepts_exactly_32_artifacts() -> None:
    parsing = _parsing_module()
    raw_output = "\n".join(f"```python\nprint({index})\n```" for index in range(32))

    parsed_output = parsing.parse_cli_output(raw_output)

    assert len(parsed_output.artifacts) == 32


def test_parse_cli_output_rejects_oversized_artifact() -> None:
    parsing = _parsing_module()
    large_content = "x" * (128 * 1024 + 1)
    raw_output = f"```python\n{large_content}\n```"

    with pytest.raises(parsing.ParsingArtifactError, match="Artifact"):
        parsing.parse_cli_output(raw_output)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_parse_cli_output_handles_empty_string() -> None:
    parsing = _parsing_module()

    parsed_output = parsing.parse_cli_output("")

    assert parsed_output.stdout_raw == ""
    assert parsed_output.artifacts == []


def test_parse_cli_output_handles_only_whitespace() -> None:
    parsing = _parsing_module()

    parsed_output = parsing.parse_cli_output("   \n  \n  ")

    assert parsed_output.artifacts == []


@pytest.mark.parametrize(
    "language_tag",
    ["python", "Python", "PYTHON", "py"],
    ids=["lowercase", "capitalized", "uppercase", "py-alias"],
)
def test_parse_cli_output_normalizes_python_language_variants(language_tag: str) -> None:
    parsing = _parsing_module()
    raw_output = f"```{language_tag}\ndef f(): pass\n```"

    parsed_output = parsing.parse_cli_output(raw_output)

    assert parsed_output.artifacts[0].language == "python"
