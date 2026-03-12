from __future__ import annotations

import ast
import re

from pydantic import BaseModel, ConfigDict, Field

from aignt_os.security import (
    mask_secrets,
    normalize_unicode,
    strip_ansi_sequences,
    strip_bidi_controls,
)

FENCED_BLOCK_RE = re.compile(
    r"```(?P<language>[^\n`]*)\n(?P<content>.*?)```",
    re.DOTALL,
)
MAX_RAW_OUTPUT_SIZE = 1024 * 1024
MAX_ARTIFACT_COUNT = 32
MAX_ARTIFACT_SIZE = 128 * 1024
TRANSPORT_NOISE_PREFIXES = ("[transport]",)
_UNSAFE_SUBPROCESS_FUNCTIONS = {
    "run",
    "call",
    "check_call",
    "check_output",
    "Popen",
}


class ParsingArtifactError(ValueError):
    pass


class ParsedArtifact(BaseModel):
    model_config = ConfigDict(strict=True)

    language: str | None = None
    content: str = Field(min_length=1)


class ParsedOutput(BaseModel):
    model_config = ConfigDict(strict=True)

    stdout_raw: str
    stdout_clean: str
    artifacts: list[ParsedArtifact] = Field(default_factory=list)


def parse_cli_output(raw_output: str) -> ParsedOutput:
    _validate_raw_output_size(raw_output)
    clean_output = _clean_output(raw_output)
    artifacts = _extract_fenced_blocks(clean_output)
    return ParsedOutput(
        stdout_raw=raw_output,
        stdout_clean=mask_secrets(clean_output),
        artifacts=artifacts,
    )


def validate_python_artifact(artifact: ParsedArtifact) -> None:
    if artifact.language not in {"python", "py"}:
        return

    _validate_python_source(artifact.content)


def validate_named_artifact_content(artifact_name: str, content: str) -> None:
    if not is_python_artifact_name(artifact_name):
        return

    _validate_python_source(content)


def is_python_artifact_name(artifact_name: str) -> bool:
    normalized_name = artifact_name.strip().lower()
    return normalized_name.endswith((".py", "_py", "_python"))


def _validate_python_source(source: str) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ParsingArtifactError("Python artifact is invalid.") from exc

    finding = _find_unsafe_python_construct(tree)
    if finding is not None:
        raise ParsingArtifactError(f"Python artifact is unsafe: {finding}.")


def _find_unsafe_python_construct(tree: ast.AST) -> str | None:
    module_aliases: dict[str, str] = {}
    function_aliases: dict[str, tuple[str, str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"os", "subprocess"}:
                    module_aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module in {"os", "subprocess"}:
            for alias in node.names:
                function_aliases[alias.asname or alias.name] = (node.module, alias.name)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                return node.func.id

            aliased_function = function_aliases.get(node.func.id)
            if aliased_function == ("os", "system"):
                return "os.system"
            if (
                aliased_function is not None
                and aliased_function[0] == "subprocess"
                and aliased_function[1] in _UNSAFE_SUBPROCESS_FUNCTIONS
                and _call_uses_shell_true(node)
            ):
                return f"subprocess.{aliased_function[1]}(..., shell=True)"

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            module_name = module_aliases.get(node.func.value.id)
            if module_name == "os" and node.func.attr == "system":
                return "os.system"
            if (
                module_name == "subprocess"
                and node.func.attr in _UNSAFE_SUBPROCESS_FUNCTIONS
                and _call_uses_shell_true(node)
            ):
                return f"subprocess.{node.func.attr}(..., shell=True)"

    return None


def _call_uses_shell_true(node: ast.Call) -> bool:
    for keyword in node.keywords:
        if keyword.arg != "shell":
            continue
        if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
            return True
    return False


def _clean_output(raw_output: str) -> str:
    without_ansi = strip_ansi_sequences(strip_bidi_controls(normalize_unicode(raw_output)))
    cleaned_lines: list[str] = []
    inside_fence = False

    for line in without_ansi.splitlines():
        if line.startswith("```"):
            inside_fence = not inside_fence
            cleaned_lines.append(line)
            continue

        if not inside_fence and _is_operational_noise(line):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def _is_operational_noise(line: str) -> bool:
    stripped_line = line.strip()
    return stripped_line.startswith(TRANSPORT_NOISE_PREFIXES)


def _extract_fenced_blocks(clean_output: str) -> list[ParsedArtifact]:
    artifacts: list[ParsedArtifact] = []

    for match in FENCED_BLOCK_RE.finditer(clean_output):
        if len(artifacts) >= MAX_ARTIFACT_COUNT:
            raise ParsingArtifactError("Too many artifacts extracted.")

        language = _normalize_language(match.group("language"))
        content = match.group("content").strip()
        if not content:
            continue
        if len(content) > MAX_ARTIFACT_SIZE:
            raise ParsingArtifactError("Artifact is too large.")
        artifacts.append(ParsedArtifact(language=language, content=content))

    return artifacts


def _validate_raw_output_size(raw_output: str) -> None:
    if len(raw_output) > MAX_RAW_OUTPUT_SIZE:
        raise ParsingArtifactError("Raw output is too large.")


def _normalize_language(language: str) -> str | None:
    normalized_language = language.strip().lower()
    if not normalized_language:
        return None
    if normalized_language == "py":
        return "python"
    return normalized_language
