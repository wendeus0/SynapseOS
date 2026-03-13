from importlib import import_module
from pathlib import Path

import pytest


def _security_module():
    return import_module("aignt_os.security")


def test_strip_bidi_controls_removes_direction_override_characters() -> None:
    security = _security_module()

    value = "safe\u202etext\u2066here\u2069"

    assert security.strip_bidi_controls(value) == "safetexthere"


def test_sanitize_clean_text_normalizes_unicode_masks_secrets_and_removes_ansi() -> None:
    security = _security_module()

    value = "\x1b[32mBearer secret-token\u001b[0m e\u0301 \u202eＦ"

    sanitized = security.sanitize_clean_text(value, strip_outer_whitespace=True, remove_ansi=True)

    assert "\x1b[" not in sanitized
    assert "Bearer secret-token" not in sanitized
    assert security.REDACTION_TOKEN in sanitized
    assert "é" in sanitized
    assert "\u202e" not in sanitized
    assert "F" in sanitized


def test_resolve_path_within_root_accepts_canonical_internal_path(tmp_path: Path) -> None:
    security = _security_module()

    root = tmp_path / "workspace"
    nested = root / "features" / "SPEC.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("fixture\n", encoding="utf-8")

    assert security.resolve_path_within_root(nested, root=root) == nested.resolve()


def test_resolve_path_within_root_rejects_symlink_escape(tmp_path: Path) -> None:
    security = _security_module()

    root = tmp_path / "workspace"
    outside = tmp_path / "outside.md"
    outside.write_text("fixture\n", encoding="utf-8")
    root.mkdir()
    escaped = root / "escaped.md"
    escaped.symlink_to(outside)

    with pytest.raises(ValueError):
        security.resolve_path_within_root(escaped, root=root)
