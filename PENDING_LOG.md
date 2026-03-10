# PENDING_LOG

## Decisões incorporadas recentemente

- A validação contra `main` em `pull_request` passou a usar o `head.sha` real da PR e o nome real da branch, evitando merge ref/detached ref sintético no GitHub Actions.
- O hook local `.githooks/pre-commit` ficou explicitamente leve via `./scripts/commit-check.sh --hook-mode`.
- O `DOCKER_PREFLIGHT` operacional real continua explícito e separado do hook leve, via `./scripts/docker-preflight.sh`.
- A baseline operacional do repositório foi restaurada com correções mínimas de Ruff/import order/formatação nos arquivos apontados pela revisão.
- O `commit-check.sh` passou a usar `./scripts/commit-check.sh --sync-dev` como caminho padrão para bootstrap/checks locais, com `--no-sync` explícito para rerun rápido e `--hook-mode` preservando o fluxo leve.
- A SPEC da feature e o lifecycle do runtime passaram a exigir validação adicional de identidade do processo antes de `stop`.
- O estado do runtime passou a exigir escrita atômica, permissões restritas e tratamento seguro para corrupção/adulteração local.
- O security-review final da feature considerou o escopo aprovado com ressalvas baixas e compatíveis com o MVP.
- A branch de integração `chore/merge-operational-candidates` consolidou `chore-resolve-operational-merge-conflicts`, `feat-agent-skills` e `features/f11-runtime-persistente-minimo`.
- A validação prática da feature de runtime persistente foi fechada na branch de integração com `17` testes passando em ambiente local dedicado.
- A branch `chore/devcontainer-codex-isolation` introduziu um ambiente isolado de desenvolvimento do Codex com `.devcontainer/`, `compose.dev.yaml`, `scripts/dev-codex.sh` e profile versionado em `.codex/config.toml`.
- O fluxo container-first do Codex ficou documentado em `AGENTS.md` e `README.md`, mantendo `codex-dev` separado do serviço de runtime `aignt-os`.
- A validação operacional local confirmou `codex-dev` com usuário não-root, `read_only`, `no-new-privileges`, `cap_drop: [ALL]`, sem `docker.sock`, sem mount do `$HOME` do host e com bind mount restrito ao repositório em `/workspace`.
- A Branch Sync Gate foi incorporada como regra operacional leve em `AGENTS.md`, com `./scripts/branch-sync-check.sh` para detectar drift e `./scripts/branch-sync-update.sh` para atualização conservadora da branch.
- As ressalvas baixas do security-review sobre a Branch Sync Gate foram mitigadas e o parecer final ficou aprovado, sem risco novo relevante.
- O `debug-failure` foi criado como skill própria para diagnóstico inicial de falhas reais, classificação da causa e encaminhamento para o próximo agent.
- A avaliação de ADR concluiu que a Branch Sync Gate é convenção operacional local de governança do repositório e não exige ADR nova nem atualização de ADR existente.
- A branch `feat/memory-curator-skill` abriu a frente de memória durável do repositório com a skill `memory-curator`, `memory.md` inicial e registro mínimo do papel da skill em `AGENTS.md`.
- O `memory-curator` ficou definido para consolidar decisões incorporadas, trade-offs, estado atual da frente, pendências abertas e próximos passos em `memory.md`, sem substituir `session-logger` nem `technical-triage`.
- O fluxo de fechamento por convenção operacional ficou registrado na skill `memory-curator` com as chamadas `$memory-curator encerrar conversa` e `$memory-curator close session`, deixando explícito que isso não é alias nativo da plataforma.
- A avaliação mais recente de ADR concluiu que `memory-curator` e `memory.md` não exigem ADR neste momento, por serem governança operacional local e não mudança arquitetural estável.
- A avaliação operacional desta frente fixou `./scripts/commit-check.sh --sync-dev` como caminho padrão para checks/testes locais, com `uv run --no-sync` restrito a reexecução rápida após bootstrap e virtualenv explícita apenas como fallback de diagnóstico.
- A mitigação final desta frente moveu a validação de branch para antes de qualquer resolução de fluxo e antes de qualquer `uv sync`, eliminando sincronização desnecessária antes do gate operacional.
- O `security-review` final desta frente foi concluído com aprovação sem ressalvas, mantendo a separação entre hook leve, checks locais e `DOCKER_PREFLIGHT` operacional real.
- A validação operacional do ambiente atual do Codex com `network-access = true` confirmou `git push` e `gh pr create` funcionando no sandbox normal; a governança operacional foi ajustada para refletir o sandbox como caminho padrão e manter fallback fora do sandbox apenas como contingência para falha real de rede/sandbox, sem mascarar erro de autenticação, permissão ou conectividade real do host.

## Pendências abertas

- Validar em GitHub Actions real se o job `branch-validation` continua correto em eventos `pull_request` usando `github.event.pull_request.head.sha` e `github.head_ref`.
- Validar `./scripts/docker-preflight.sh` sem `--dry-run` em ambiente com Docker acessível.
- Validar o fluxo completo de `uv sync --locked --extra dev` em ambiente com rede liberada.
- Resolver a dívida de formatação global do repositório para que `ruff format --check .` possa voltar a ser gate completo sem ressalvas.

## Pontos de atenção futuros

- `uv run --no-sync` continua dependendo de ambiente previamente sincronizado; em worktree fria ele pode cair no Python do host e falhar por dependências ausentes.
- O fluxo local com `.venv` pode exigir `PYTHONPATH=src` quando não se usa `uv run`; por isso ele continua apenas como fallback operacional e não como caminho padrão.
- O hardening do runtime valida identidade do processo por marcador + token em `/proc/<pid>/cmdline`; isso continua Linux-first.
- A validação do diretório configurável de estado permanece propositalmente básica no MVP e pode ser endurecida depois com âncora explícita no workspace.
- O runtime persistente continua propositalmente restrito a processo único local, sem scheduler, distribuição ou recuperação avançada.
- No uso diário do Codex em container, prefira `./scripts/dev-codex.sh` como entrypoint principal para evitar corrida operacional com `docker compose ... up` manual sobre o mesmo serviço.
- No uso diário de sincronização com `main`, prefira `./scripts/branch-sync-check.sh` e `./scripts/branch-sync-update.sh` em vez de comandos Git ad hoc; a atualização automática continua propositalmente conservadora e pode exigir resolução manual.
- `memory.md` deve permanecer memória durável e reaproveitável, sem virar transcrição de conversa.
- O `memory-curator` deve consolidar estado e handoff, enquanto `ERROR_LOG.md` e `PENDING_LOG.md` seguem como trilha operacional detalhada.

## Itens que podem virar novas features ou ajustes futuros

- Endurecimento adicional do path de estado para restringir explicitamente a uma raiz confiável do workspace.
- Melhoria de portabilidade do runtime além de Linux, caso isso entre no escopo futuro.
- Documentação operacional curta para bootstrap local (`--sync-dev`) e para o lifecycle do runtime persistente.
- Limpeza operacional do repositório para remover debt de formatação fora do escopo desta feature.
