from importlib import import_module
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "specs"


def _validator_module():
    return import_module("aignt_os.specs.validator")


def test_valid_spec_file_returns_structured_document() -> None:
    validator = _validator_module()

    document = validator.validate_spec_file(FIXTURES_DIR / "valid_feature_spec.md")

    assert document.metadata.id == "F02-spec-engine-mvp"
    assert document.metadata.type == "feature"
    assert document.metadata.acceptance_criteria == ["YAML front matter is required."]
    assert "Contexto" in document.sections
    assert "Objetivo" in document.sections


def test_spec_without_yaml_front_matter_is_rejected() -> None:
    validator = _validator_module()

    with pytest.raises(validator.SpecValidationError, match="front matter"):
        validator.validate_spec_file(FIXTURES_DIR / "invalid_missing_yaml_spec.md")


def test_spec_requires_non_empty_acceptance_criteria() -> None:
    validator = _validator_module()

    with pytest.raises(validator.SpecValidationError, match="acceptance_criteria"):
        validator.validate_spec_file(FIXTURES_DIR / "invalid_acceptance_criteria_spec.md")


def test_spec_requires_context_section() -> None:
    validator = _validator_module()

    with pytest.raises(validator.SpecValidationError, match="Contexto"):
        validator.validate_spec_file(FIXTURES_DIR / "invalid_missing_context_spec.md")
