from __future__ import annotations

from pathlib import Path

CHANGELOG_PATH = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
README_PATH = Path(__file__).resolve().parents[2] / "README.md"
FEATURES_ROOT = Path(__file__).resolve().parents[2] / "features"


def test_readme_documents_watch_cancel_and_actual_dashboard_shortcuts() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## TUI Watch e Cancelamento Local" in readme
    assert "`aignt runs watch <run_id>`" in readme
    assert "`aignt runs cancel <run_id>`" in readme
    assert "`Enter`" in readme
    assert "`a`" in readme
    assert "`f`" in readme
    assert "`r`" in readme
    assert "`x`" in readme
    assert "`k`" in readme
    assert "cancelamento atual e apenas local e gracioso" in readme
    assert "nao ha scheduler, fila remota de cancelamento nem coordenacao multi-host" in readme


def test_f40_and_f42_have_minimum_feature_artifacts() -> None:
    for feature_name in ("F40-local-cancellation", "F42-tui-filters"):
        feature_dir = FEATURES_ROOT / feature_name

        assert (feature_dir / "SPEC.md").exists()
        assert (feature_dir / "NOTES.md").exists()
        assert (feature_dir / "CHECKLIST.md").exists()
        assert (feature_dir / "REPORT.md").exists()


def test_changelog_mentions_filters_and_local_cancellation() -> None:
    changelog = CHANGELOG_PATH.read_text(encoding="utf-8")

    assert "## Unreleased" in changelog
    assert (
        "dashboard TUI com filtros visuais por falha (`f`), atividade (`r`) e "
        "restauracao da lista completa (`x`)" in changelog
    )
    assert (
        "`aignt runs cancel <run_id>` e atalho `k` no dashboard para "
        "cancelamento local e gracioso de runs" in changelog
    )
