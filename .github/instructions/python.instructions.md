---
applyTo: "**/*.py"
---

# Python — Instruções de contexto

## Gerenciamento de ambiente

- Use sempre `uv` para gerenciar dependências — nunca `pip install` direto.
- Para executar ferramentas do projeto: `uv run --no-sync <comando>`.
- Para adicionar dependências: `uv add <pacote>` (runtime) ou `uv add --dev <pacote>` (dev).
- Nunca modifique `.venv/` diretamente.

## Execução de checks

```bash
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync python -m mypy
uv run --no-sync python -m pytest
```

Use `python -m pytest` e `python -m mypy` — não os wrappers bare (`pytest`, `mypy`).

## Qualidade de código

- Siga as configurações de `ruff` em `pyproject.toml` — não desative regras sem justificativa.
- Prefira `strict=False` explícito em `zip()` para satisfazer `B905`.
- Typing: use anotações explícitas em todas as funções públicas.
- Evite `# type: ignore` salvo em casos de libs sem stubs documentados; comente o motivo.

## Estrutura do projeto

- Código de produção em `src/aignt_os/`.
- Layout: `src/aignt_os/<módulo>/` com `__init__.py` explícito.
- Contratos em `src/aignt_os/contracts.py` — preserve as distinções existentes (ex: `stdout_raw` vs `stdout_clean`).
- Configurações via `src/aignt_os/config.py` com Pydantic Settings — não use `os.environ` diretamente.

## Pydantic e contratos

- Use Pydantic v2 (`model_validator`, `field_validator`, não `validator`).
- `BaseModel` para contratos de dados; `BaseSettings` para configuração de ambiente.
- Campos obrigatórios sem default — não use `Optional` quando o campo é realmente obrigatório.

## Imports

- Imports absolutos: `from aignt_os.contracts import ...`
- Não use imports relativos (`from ..contracts import ...`) exceto dentro do mesmo subpacote.
- Ordem: stdlib → third-party → local (ruff isort cuida disso automaticamente).

## Proibições

- Não crie módulos fora de `src/aignt_os/` para código de produção.
- Não adicione dependências pesadas sem justificativa alinhada ao MVP.
- Não antecipe subsistemas não implementados (`adapters/`, `orchestrator/`, `pipeline/`, `memory/`, `db/`).
