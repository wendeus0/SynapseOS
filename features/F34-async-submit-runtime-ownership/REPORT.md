# F34 Report

## Resumo executivo

- A `F34-async-submit-runtime-ownership` fecha o gap de ownership no `runs submit` autenticado quando o dispatch resolve para `async`.
- O gate reaproveita o binding `started_by` entregue pela `F32` e mantém o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS.
- O recorte permaneceu local-only: sem socket, sem IPC, sem alteracao no worker e sem mudanca no caminho `sync`.

## Escopo alterado

- `RunDispatchService` passa a aceitar provider opcional do estado do runtime e aplica gate de ownership apenas para dispatch resolvido como `async`
- `runs submit` mapeia ausencia de runtime pronto para `Environment error` e mismatch de principal para `Authorization error`
- novos testes unitarios travam ausencia de runtime, mismatch de owner e fallback legado no dispatch
- novos testes de integracao travam `async` e `auto -> async` pela CLI autenticada
- `SPEC.md`, `NOTES.md`, `CHECKLIST.md` e este `REPORT.md` adicionados para a `F34`

## Validacoes executadas

- `validate_spec_file(Path('features/F34-async-submit-runtime-ownership/SPEC.md'))`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m pytest tests/unit/test_runtime_dispatch.py tests/integration/test_cli_auth_rbac.py -q`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m pytest tests/unit/test_runtime_dispatch.py tests/integration/test_cli_auth_rbac.py tests/integration/test_runs_submit_cli.py tests/integration/test_worker_runtime_flow.py -q`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync ruff check src/aignt_os/cli/app.py src/aignt_os/runtime/dispatch.py tests/unit/test_runtime_dispatch.py tests/integration/test_cli_auth_rbac.py`
- `env UV_CACHE_DIR=/home/g0dsssp33d/work/projects/aignt-os/.cache/uv uv run --no-sync python -m mypy src/aignt_os/cli/app.py src/aignt_os/runtime/dispatch.py`
- `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security`
- `./scripts/security-gate.sh`

## Review de seguranca

- Parecer final: aprovado.
- Riscos revisados:
  - enfileiramento autenticado de run assíncrona sem runtime residente pronto
  - submissao autenticada para runtime iniciado por outro principal
  - regressao do comportamento sem auth ou no caminho `sync`
- Mitigacoes aplicadas:
  - o gate so roda para dispatch resolvido como `async`
  - a CLI reutiliza o modelo de erros existente, sem criar bypass operacional novo
  - o fallback legado sem `started_by` permanece explicito e testado

## Riscos residuais

- Runtime legado sem `started_by` continua aceitando submit autenticado em `async` por compatibilidade.
- O worker continua sem enforcement posterior de ownership; esta frente deliberadamente bloqueia o problema no submit, sem ampliar o recorte.

## Proximos passos

- Rodar `branch-sync-guard` antes de commit/push/PR se a frente for finalizada fora de `main`.
- Se houver novo slice de `resident_transport_auth`, ele deve decidir explicitamente se ownership diferido no worker ainda cabe sem transporte novo.

## Status final da frente

- `READY_FOR_COMMIT`
