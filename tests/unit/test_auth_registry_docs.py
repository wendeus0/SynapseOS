from __future__ import annotations

from pathlib import Path

README_PATH = Path(__file__).resolve().parents[2] / "README.md"
IDEAS_PATH = Path(__file__).resolve().parents[2] / "docs" / "IDEAS.md"


def test_readme_documents_local_auth_registry_cli_boundary() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Auth Registry Local" in readme
    assert "`aignt auth init --principal-id local-operator`" in readme
    assert "`aignt auth issue --principal-id local-operator`" in readme
    assert "`aignt auth disable --token-id <token_id>`" in readme
    assert "nao abre socket" in readme.lower()


def test_ideas_reflects_f28_f29_f30_and_f31_g11_decomposition() -> None:
    ideas = IDEAS_PATH.read_text(encoding="utf-8")

    assert (
        "| G-09 | Circuit breaker para adapters (estado persistido entre runs) | medium | L | "
        "absorbed em `F28` | — |" in ideas
    )
    assert (
        "| G-11 | Autenticação e autorização (fundacao local absorvida; transporte autenticado "
        "residente e operacao remota ainda pendentes) | low | XL | decomposed em `F31`; "
        "fundacao local absorvida em `F29`/`F30` | pós-F27 |" in ideas
    )
    assert "- `F30`: provisionamento local do auth registry (`init`, `issue`, `disable`)" in ideas
    assert "- `F31`: decomposicao formal de `G-11` em buckets local, residente e remoto" in ideas
