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


def test_ideas_reflects_f28_f29_f30_f31_and_post_f36_g11_state() -> None:
    ideas = IDEAS_PATH.read_text(encoding="utf-8")

    assert (
        "| G-09 | Circuit breaker para adapters (estado persistido entre runs) | medium | L | "
        "absorbed em `F28` | — |" in ideas
    )
    assert (
        "| G-11 | Autenticação e autorização (fundacao local absorvida; bucket residente "
        "local absorvido; operacao remota ainda pendente) | low | XL | decomposed em "
        "`F31`; local absorvido em `F29`/`F30`; residente local absorvido em "
        "`F32`/`F34`/`F35`/`F36` "
        "| pós-F27 |" in ideas
    )
    assert "- `F30`: provisionamento local do auth registry (`init`, `issue`, `disable`)" in ideas
    assert "- `F31`: decomposicao formal de `G-11` em buckets local, residente e remoto" in ideas
    assert (
        "- `F32`: primeiro slice de `resident_transport_auth` com binding local de "
        "`started_by` no lifecycle do runtime" in ideas
    )
    assert (
        "- `F34`: gate de ownership no `runs submit` quando o dispatch resolve para "
        "`async`" in ideas
    )
    assert (
        "- `F35`: filtro de ownership no consumo da fila pelo worker do runtime residente" in ideas
    )
    assert (
        "- `F36`: observabilidade de `runtime_owner_skip` para runs incompatíveis no worker "
        "autenticado" in ideas
    )
    assert (
        "- `remote_multi_host_auth`: continua sem transporte em rede, operacao entre "
        "hosts ou coordenacao remota" in ideas
    )
