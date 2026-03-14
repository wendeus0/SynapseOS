from __future__ import annotations

from pathlib import Path

README_PATH = Path(__file__).resolve().parents[2] / "README.md"


def test_readme_describes_current_baseline_instead_of_stopping_at_phase_2() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Baseline Atual do Repositório" in readme
    assert "guardrails pos-release absorvidos (`F23 -> F27`)" in readme
    assert "auth local e RBAC absorvidos (`F29`, `F30`, `F44`, `F47`)" in readme
    assert "ownership local do runtime absorvida (`F32`, `F34`, `F35`, `F36`)" in readme
    assert (
        "dashboard TUI local e observabilidade adicional absorvidos (`F40`, `F41`, `F42`, `F45`)"
        in readme
    )
    assert "robustez de runtime absorvida (`F43`)" in readme
    assert "## Estado Atual do Projeto" in readme
    assert "docs/operations/LIFECYCLE.md" in readme


def test_readme_lists_current_public_cli_surface_and_boundaries() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "### Superfície pública atual da CLI" in readme
    assert "`aignt runs watch <run_id>`" in readme
    assert "`aignt runs cancel <run_id>`" in readme
    assert "`aignt auth init|issue|disable`" in readme
    assert "`aignt runtime start|status|run|ready|stop`" in readme
    assert "nao existe web UI nem operacao distribuida" in readme
    assert "auth e RBAC continuam locais com provider `file`" in readme
