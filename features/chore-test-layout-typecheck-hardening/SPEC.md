---
id: F12-test-layout-typecheck-hardening
type: chore
summary: Endurecer o layout da arvore de testes para permitir typecheck amplo sem colisao entre modulos `conftest`.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - pyproject.toml
outputs:
  - stable_test_package_layout
  - typecheck_regression_tests
constraints:
  - manter o fluxo oficial `./scripts/commit-check.sh --sync-dev` como caminho operacional padrao
  - nao alterar logica de produto, runtime, pipeline ou adapters
  - nao introduzir dependencia de Docker nesta frente
  - manter o AIgnt-Synapse-Flow como engine propria de pipeline do AIgnt OS sem mudancas comportamentais
acceptance_criteria:
  - `uv run mypy src tests` nao falha mais por `Duplicate module named "conftest"`.
  - `uv run --no-sync python -m mypy` continua verde no fluxo oficial do repositório.
  - `pytest` continua descobrindo e executando a suite sem regressao causada pelo layout de `tests/`.
  - Existe pelo menos um teste de regressao automatizado cobrindo o typecheck amplo da arvore de testes.
non_goals:
  - alterar a configuracao operacional do Docker
  - reabrir a F09 ou mudar contratos de produto
  - trocar o fluxo oficial de checks locais
  - corrigir problemas antigos de `.venv` fora do caminho oficial
---

# Contexto

Com a F09 encerrada, a baseline oficial do repositório está saudável no fluxo suportado por `./scripts/commit-check.sh --sync-dev`, `pytest`, `ruff` e `uv run --no-sync python -m mypy`. O erro persistente restante é operacional e localizado: uma invocação ampla de `uv run mypy src tests` falha porque `tests/unit/conftest.py` e `tests/integration/conftest.py` colidem como módulos top-level.

# Objetivo

Mitigar esse erro persistente com a menor mudança possível no layout/configuração de testes:

- estabilizar o namespace da árvore `tests/`;
- preservar a descoberta do `pytest`;
- manter intacto o fluxo oficial de validação local do repositório.

# Escopo

## Incluído

- ajustes mínimos no layout/configuração da árvore `tests/`
- testes de regressão para o comando amplo de `mypy`
- validação local do fluxo oficial e do comando amplo

## Fora de escopo

- qualquer mudança em código de produto
- mudanças no runtime dual ou no worker
- mudança de ergonomia do `commit-check.sh`
- Docker, CI remoto e outras automações fora do typecheck

# Requisitos funcionais

1. O repositório deve suportar typecheck amplo sobre `src tests`.
2. A mitigação não deve quebrar a descoberta de fixtures do `pytest`.
3. O fluxo oficial `uv run --no-sync python -m mypy` deve permanecer válido.

# Requisitos não funcionais

- A correção deve ser pequena, reversível e local.
- A mudança deve ficar restrita a layout/configuração de testes e documentação local da chore.

# Observações

Se package markers em `tests/` causarem regressão de descoberta/import do `pytest`, a frente deve cair para ajuste explícito de configuração do `mypy`, sem ampliar o escopo além desta chore.
