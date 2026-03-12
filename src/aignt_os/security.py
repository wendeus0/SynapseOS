from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BIDI_CONTROL_RE = re.compile(r"[\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]")
DEFAULT_SECRET_MASK_PATTERNS: tuple[str, ...] = (
    r"ghp_[A-Za-z0-9_]+",
    r"ghs_[A-Za-z0-9_]+",
    r"(?i)Bearer [A-Za-z0-9._-]+",
    r"sk-[A-Za-z0-9]+",
)
REDACTION_TOKEN = "[REDACTED]"


def normalize_unicode(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def strip_bidi_controls(value: str) -> str:
    return BIDI_CONTROL_RE.sub("", value)


def strip_ansi_sequences(value: str) -> str:
    return ANSI_ESCAPE_RE.sub("", value)


def mask_secrets(
    value: str,
    *,
    patterns: Sequence[str] | None = None,
    replacement: str = REDACTION_TOKEN,
) -> str:
    masked = value
    for pattern in patterns or DEFAULT_SECRET_MASK_PATTERNS:
        masked = re.sub(pattern, replacement, masked)
    return masked


def sanitize_clean_text(
    value: str,
    *,
    mask_patterns: Sequence[str] | None = None,
    remove_ansi: bool = False,
    strip_outer_whitespace: bool = False,
) -> str:
    sanitized = normalize_unicode(value)
    sanitized = strip_bidi_controls(sanitized)
    if remove_ansi:
        sanitized = strip_ansi_sequences(sanitized)
    sanitized = mask_secrets(sanitized, patterns=mask_patterns)
    if strip_outer_whitespace:
        return sanitized.strip()
    return sanitized
