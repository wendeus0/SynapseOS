# F18 Report

## Escopo alterado

- Formalizacao da F18 como caminho canonico publico `runs submit -> runs show`.
- Novo teste de integracao cobrindo a sequencia completa da CLI publica no recorte sincronizado.
- Ajuste localizado no rendering para diferenciar `completed @ SPEC_VALIDATION` de outros terminais `completed`.

## Validacoes executadas

- `uv run --no-sync pytest tests/integration/test_runs_submit_cli.py tests/integration/test_runs_cli.py tests/unit/test_cli_runs_rendering.py`
- `uv run --no-sync ruff check src/aignt_os/cli/rendering.py tests/integration/test_runs_submit_cli.py tests/unit/test_cli_runs_rendering.py`
- `uv run --no-sync python -m mypy src/aignt_os/cli/rendering.py`
- `./scripts/security-gate.sh`

## Riscos residuais

- O happy path canonico continua limitado ao menor terminal publico estavel atual: `completed @ SPEC_VALIDATION`.
- A frente nao promove ainda um caminho oficial publico ate `PLAN`, `TEST_RED` ou `DOCUMENT`.
- O fluxo assincrono continua fora do caminho primario da F18, embora siga coberto pela F15.

## Proximos passos

- Usar `branch-sync-guard` antes de qualquer commit, push ou PR fora de `main`.
- Encaminhar a frente para fluxo Git apenas se houver decisao explicita de commitar esta feature agora.
