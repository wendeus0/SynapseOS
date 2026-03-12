from __future__ import annotations

from pathlib import Path

CHANGELOG_PATH = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
README_PATH = Path(__file__).resolve().parents[2] / "README.md"
RELEASE_NOTES_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "release" / "phase-2-technical-release.md"
)


def test_release_readiness_docs_cover_public_surface_and_preview_boundary() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Artifact Preview" in readme
    assert "`aignt runs show <run_id> --preview report`" in readme
    assert "`aignt runs show <run_id> --preview PLAN.clean`" in readme
    assert "`raw_output`" in readme
    assert "sync-first" in readme


def test_changelog_and_release_notes_capture_phase_2_technical_release() -> None:
    changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    release_notes = RELEASE_NOTES_PATH.read_text(encoding="utf-8")

    assert "# Changelog" in changelog
    assert "## 0.1.0" in changelog
    assert "`aignt doctor`" in changelog
    assert "`aignt runs submit <spec_path>`" in changelog
    assert "`aignt runs show <run_id> --preview report`" in changelog

    assert "# Phase 2 Technical Release" in release_notes
    assert "AIgnt-Synapse-Flow" in release_notes
    assert "`aignt doctor`" in release_notes
    assert "`aignt runs show <run_id> --preview report`" in release_notes
    assert "sync-first" in release_notes
