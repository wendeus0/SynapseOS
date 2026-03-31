from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from synapse_os.runtime_contracts import HookConfig


class SpecValidationError(ValueError):
    pass


VALID_HOOK_POINTS = {
    "pre_step",
    "post_step",
    "pre_state_transition",
    "post_state_transition",
}


class SpecMetadata(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)
    non_goals: list[str]
    hooks: list[HookConfig] = Field(default_factory=list)


class SpecDocument(BaseModel):
    model_config = ConfigDict(strict=True)

    metadata: SpecMetadata
    sections: dict[str, str]
    body: str


def validate_spec_file(path: Path) -> SpecDocument:
    text = path.read_text(encoding="utf-8")
    metadata_block, body = _split_front_matter(text)
    metadata = _load_metadata(metadata_block)
    sections = _parse_sections(body)
    _require_sections(sections, required_sections=("Contexto", "Objetivo"))
    return SpecDocument(metadata=metadata, sections=sections, body=body.strip())


def _split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise SpecValidationError("SPEC requires front matter YAML.")

    closing_marker = "\n---\n"
    closing_index = text.find(closing_marker, len("---\n"))
    if closing_index == -1:
        raise SpecValidationError("SPEC requires front matter YAML.")

    metadata_block = text[len("---\n") : closing_index]
    body = text[closing_index + len(closing_marker) :]
    return metadata_block, body


def _load_metadata(metadata_block: str) -> SpecMetadata:
    try:
        raw_metadata = yaml.safe_load(metadata_block)
    except yaml.YAMLError as exc:
        raise SpecValidationError("SPEC front matter YAML is invalid.") from exc

    if not isinstance(raw_metadata, dict):
        raise SpecValidationError("SPEC front matter YAML is invalid.")

    _validate_hooks_in_raw_metadata(raw_metadata)

    try:
        return SpecMetadata.model_validate(raw_metadata)
    except ValidationError as exc:
        message = exc.errors()[0]["loc"][0]
        raise SpecValidationError(f"SPEC metadata is invalid: {message}") from exc


def _validate_hooks_in_raw_metadata(raw_metadata: dict[str, object]) -> None:
    if "hooks" not in raw_metadata:
        return
    hooks_raw = raw_metadata["hooks"]
    if not isinstance(hooks_raw, list):
        raise SpecValidationError("SPEC metadata is invalid: hooks must be a list")
    for i, hook in enumerate(hooks_raw):
        if not isinstance(hook, dict):
            raise SpecValidationError(
                f"SPEC metadata is invalid: hooks[{i}] must be a dict"
            )
        if "handler" not in hook or not hook["handler"]:
            raise SpecValidationError(
                f"SPEC metadata is invalid: hooks[{i}].handler is required"
            )
        if "point" not in hook:
            raise SpecValidationError(
                f"SPEC metadata is invalid: hooks[{i}].point is required"
            )
        if hook["point"] not in VALID_HOOK_POINTS:
            raise SpecValidationError(
                f"SPEC metadata is invalid: hooks[{i}].point '{hook['point']}' is not valid"
            )


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in body.splitlines():
        if line.startswith("# "):
            current_section = line[2:].strip()
            sections[current_section] = []
            continue

        if current_section is not None:
            sections[current_section].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _require_sections(
    sections: dict[str, str], required_sections: tuple[str, ...]
) -> None:
    for section in required_sections:
        if section not in sections or not sections[section]:
            raise SpecValidationError(f"SPEC requires section '{section}'.")
