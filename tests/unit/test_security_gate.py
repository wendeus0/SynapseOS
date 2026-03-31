from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from synapse_os.security import (
    REDACTION_TOKEN,
    compute_file_sha256,
    mask_secrets,
    normalize_unicode,
    resolve_path_within_root,
    sanitize_clean_text,
    strip_ansi_sequences,
    strip_bidi_controls,
)


class TestNormalizeUnicode:
    def test_normalize_unicode_converts_nfkc(self) -> None:
        nfd_text = "cafe\u0301"
        result = normalize_unicode(nfd_text)
        assert result == "café"
        assert result == "\u00e9".join(["caf", ""])

    def test_normalize_unicode_handles_fullwidth(self) -> None:
        fullwidth = "ＡＢＣ"
        result = normalize_unicode(fullwidth)
        assert result == "ABC"


class TestStripBidiControls:
    def test_strip_bidi_controls_removes_directional_chars(self) -> None:
        text = "hello\u202eworld\u200etest"
        result = strip_bidi_controls(text)
        assert result == "helloworldtest"

    def test_strip_bidi_controls_removes_all_bidi_controls(self) -> None:
        text = "\u202aleft\u202bright\u2066isolate"
        result = strip_bidi_controls(text)
        assert result == "leftrightisolate"


class TestStripAnsiSequences:
    def test_strip_ansi_sequences_removes_color_codes(self) -> None:
        text = "\x1b[31mred\x1b[0m normal"
        result = strip_ansi_sequences(text)
        assert result == "red normal"

    def test_strip_ansi_sequences_handles_complex_codes(self) -> None:
        text = "\x1b[1;32mOK\x1b[0m \x1b[38;5;200mpink"
        result = strip_ansi_sequences(text)
        assert result == "OK pink"


class TestMaskSecrets:
    def test_mask_secrets_hides_github_tokens(self) -> None:
        text = "token: ghp_abc123secret"
        result = mask_secrets(text)
        assert "ghp_abc123secret" not in result
        assert REDACTION_TOKEN in result

    def test_mask_secrets_hides_github_server_tokens(self) -> None:
        text = "auth: ghs_server123"
        result = mask_secrets(text)
        assert "ghs_server123" not in result
        assert REDACTION_TOKEN in result

    def test_mask_secrets_hides_bearer_tokens(self) -> None:
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9"
        result = mask_secrets(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert REDACTION_TOKEN in result

    def test_mask_secrets_hides_openai_keys(self) -> None:
        text = "api_key: sk-proj-abc123xyz"
        result = mask_secrets(text)
        assert "sk-proj-abc123xyz" not in result
        assert REDACTION_TOKEN in result

    def test_mask_secrets_custom_patterns(self) -> None:
        text = "secret: MY_SECRET_123"
        result = mask_secrets(text, patterns=[r"MY_SECRET_\d+"])
        assert "MY_SECRET_123" not in result
        assert REDACTION_TOKEN in result

    def test_mask_secrets_no_secrets_unchanged(self) -> None:
        text = "hello world"
        result = mask_secrets(text)
        assert result == text


class TestSanitizeCleanText:
    def test_sanitize_clean_text_combines_all_sanitizers(self) -> None:
        text = "\x1b[31mBearer sk-key123\u202eＦ"
        result = sanitize_clean_text(text, remove_ansi=True)
        assert "Bearer" not in result
        assert "sk-key123" not in result
        assert "\u202e" not in result
        assert "\x1b[" not in result

    def test_sanitize_clean_text_strips_outer_whitespace(self) -> None:
        text = "  hello  "
        result = sanitize_clean_text(text, strip_outer_whitespace=True)
        assert result == "hello"

    def test_sanitize_clean_text_preserves_content_when_no_flags(self) -> None:
        text = "hello world"
        result = sanitize_clean_text(text)
        assert result == "hello world"


class TestResolvePathWithinRoot:
    def test_resolve_path_within_root_accepts_valid_path(self, tmp_path: Path) -> None:
        child = tmp_path / "subdir" / "file.txt"
        child.parent.mkdir(parents=True, exist_ok=True)
        child.touch()
        result = resolve_path_within_root(child, root=tmp_path)
        assert result.is_absolute()
        assert str(result).startswith(str(tmp_path.resolve()))

    def test_resolve_path_within_root_rejects_traversal(self, tmp_path: Path) -> None:
        escape_path = tmp_path / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="Path escapes trusted root"):
            resolve_path_within_root(escape_path, root=tmp_path)

    def test_resolve_path_within_root_rejects_symlink_escape(
        self, tmp_path: Path
    ) -> None:
        outside = tmp_path.parent / "outside.txt"
        outside.touch()
        link = tmp_path / "escape_link"
        link.symlink_to(outside)
        with pytest.raises(ValueError, match="Path escapes trusted root"):
            resolve_path_within_root(link, root=tmp_path)


class TestComputeFileSha256:
    def test_compute_file_sha256_returns_correct_hash(self, tmp_path: Path) -> None:
        content = b"hello world"
        expected = hashlib.sha256(content).hexdigest()
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)
        result = compute_file_sha256(file_path)
        assert result == expected

    def test_compute_file_sha256_empty_file(self, tmp_path: Path) -> None:
        expected = hashlib.sha256(b"").hexdigest()
        file_path = tmp_path / "empty.txt"
        file_path.write_bytes(b"")
        result = compute_file_sha256(file_path)
        assert result == expected
