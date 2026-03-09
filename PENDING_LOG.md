# PENDING_LOG

## Decisões incorporadas recentemente

- A validação contra `main` em `pull_request` passou a usar o `head.sha` real da PR e o nome real da branch, evitando merge ref/detached ref sintético no GitHub Actions.
- O hook local `.githooks/pre-commit` ficou explicitamente leve via `./scripts/commit-check.sh --hook-mode`.
- O `DOCKER_PREFLIGHT` operacional real continua explícito e separado do hook leve, via `./scripts/docker-preflight.sh`.
- A baseline operacional do repositório foi restaurada com correções mínimas de Ruff/import order/formatação nos arquivos apontados pela revisão.
- O `commit-check.sh` passou a usar `uv run --no-sync` por padrão e reserva `--sync-dev` para bootstrap explícito de dependências dev.
- A SPEC e o lifecycle do runtime passaram a exigir validação adicional de identidade do processo antes de `stop`.
- O estado do runtime passou a exigir escrita atômica, permissões restritas e tratamento seguro para corrupção/adulteração local.
- O security-review final da feature considerou o escopo aprovado com ressalvas baixas e compatíveis com o MVP.

## Pendências abertas

- Validar em GitHub Actions real se o job `branch-validation` continua correto em eventos `pull_request` usando `github.event.pull_request.head.sha` e `github.head_ref`.
- Validar `./scripts/docker-preflight.sh` sem `--dry-run` em ambiente com Docker acessível.
- Validar o fluxo completo de `uv sync --locked --extra dev` em ambiente com rede liberada.
- Documentar no fluxo local que `scripts/commit-check.sh` agora usa `uv run --no-sync` por padrão e requer `--sync-dev` para bootstrap explícito.
- Resolver a dívida de formatação global do repositório para que `ruff format --check .` possa voltar a ser gate completo sem ressalvas.

## Pontos de atenção futuros

- O fluxo local com `.venv` pode exigir `PYTHONPATH=src` quando não se usa `uv run`; isso ficou apenas contornado na sessão e ainda merece validação fora do sandbox.
- O hardening do runtime valida identidade do processo por marcador + token em `/proc/<pid>/cmdline`; isso continua Linux-first.
- A validação do diretório configurável de estado permanece propositalmente básica no MVP e pode ser endurecida depois com âncora explícita no workspace.
- O runtime persistente continua propositalmente restrito a processo único local, sem scheduler, distribuição ou recuperação avançada.
