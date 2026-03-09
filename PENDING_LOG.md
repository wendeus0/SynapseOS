# PENDING_LOG

## Decisões incorporadas recentemente

- A validação contra `main` em `pull_request` passou a usar o `head.sha` real da PR e o nome real da branch, evitando merge ref/detached ref sintético no GitHub Actions.
- O hook local `.githooks/pre-commit` ficou explicitamente leve via `./scripts/commit-check.sh --hook-mode`.
- O `DOCKER_PREFLIGHT` operacional real continua explícito e separado do hook leve, via `./scripts/docker-preflight.sh`.
- A baseline operacional do repositório foi restaurada com correções mínimas de Ruff/import order/formatação nos arquivos apontados pela revisão.

## Pendências abertas

- Validar em GitHub Actions real se o job `branch-validation` continua correto em eventos `pull_request` usando `github.event.pull_request.head.sha` e `github.head_ref`.
- Validar `./scripts/docker-preflight.sh` sem `--dry-run` em ambiente com Docker acessível.
- Validar o fluxo completo de `uv sync --locked --extra dev` em ambiente com rede liberada.

## Pontos de atenção futuros

- O fluxo local com `.venv` pode exigir `PYTHONPATH=src` quando não se usa `uv run`; isso ficou apenas contornado na sessão e ainda merece validação fora do sandbox.
- Os itens não rastreados `.agents/skills/session-logger/` e `docs/ai-ops/` continuam fora do escopo desta atualização e não foram alterados.
