from __future__ import annotations

import ast
import re

from pydantic import BaseModel, ConfigDict, Field

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
FENCED_BLOCK_RE = re.compile(
    r"```(?P<language>[^\n`]*)\n(?P<content>.*?)```",
    re.DOTALL,
)
MAX_RAW_OUTPUT_SIZE = 1024 * 1024
MAX_ARTIFACT_COUNT = 32
MAX_ARTIFACT_SIZE = 128 * 1024
TRANSPORT_NOISE_PREFIXES = ("[transport]",)


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
        stdout_clean=clean_output,
        artifacts=artifacts,
    )


def validate_python_artifact(artifact: ParsedArtifact) -> None:
    if artifact.language not in {"python", "py"}:
        return

    try:
        ast.parse(artifact.content)
    except SyntaxError as exc:
        raise ParsingArtifactError("Python artifact is invalid.") from exc


def _clean_output(raw_output: str) -> str:
    without_ansi = ANSI_ESCAPE_RE.sub("", raw_output)
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
