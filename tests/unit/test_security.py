from importlib import import_module


def _security_module():
    return import_module("aignt_os.security")


def test_strip_bidi_controls_removes_direction_override_characters() -> None:
    security = _security_module()

    value = "safe\u202Etext\u2066here\u2069"

    assert security.strip_bidi_controls(value) == "safetexthere"


def test_sanitize_clean_text_normalizes_unicode_masks_secrets_and_removes_ansi() -> None:
    security = _security_module()

    value = "\x1b[32mBearer secret-token\u001b[0m e\u0301 \u202EＦ"

    sanitized = security.sanitize_clean_text(value, strip_outer_whitespace=True, remove_ansi=True)

    assert "\x1b[" not in sanitized
    assert "Bearer secret-token" not in sanitized
    assert security.REDACTION_TOKEN in sanitized
    assert "é" in sanitized
    assert "\u202E" not in sanitized
    assert "F" in sanitized
