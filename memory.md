# Current project state

## Global project state

- SynapseOS é o meta-orquestrador CLI-first; o Synapse-Flow é a engine própria de pipeline do projeto.
- A baseline operacional combina `DOCKER_PREFLIGHT` leve por padrão, fluxo container-first para o Codex, Branch Sync Gate e separação entre memória durável (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- O MVP chega até `DOCUMENT`: `RUN_REPORT.md` por run, `CodexCLIAdapter` como primeiro adapter real, CLI enriquecida com Rich, observabilidade CLI de runs e TUI dashboard com explorer, filtros, log viewer e cancelamento local.
- A etapa 2 está completa em `main` (F15–F22); a primeira onda de guardrails também está completa (F23–F27).
- O baseline incorpora F28–F36 (circuit breaker, RBAC foundation, auth registry CLI, principal binding, ownership filter/worker, skip observability) e F40–F47 (cancelamento local, dashboard TUI, robustez de runtime, auth abstraction, TUI perf, RBAC por role).
- `F48-spec-validation-gate` foi mergeada em `main` via PR #91: o Synapse-Flow agora bloqueia execução de pipeline quando a SPEC não passa na validação antes de `PLAN`.
- O rename cosmético `AIgnt OS → SynapseOS` foi concluído no commit `bc9ceab` na branch `claude/rename-to-synapseos-RxaIg`: pacote Python (`synapse_os`), env prefix (`SYNAPSE_OS_`), Docker (`synapse-os`), pipeline engine (`Synapse-Flow`), runtime dirs (`.synapse-os/`), 254 arquivos atualizados.

## Local snapshot

- Branch atual: `claude/rename-to-synapseos-RxaIg` — 1 commit à frente de `main` (`bc9ceab rename: AIgnt OS → SynapseOS`), working tree limpa.
- PR do rename ainda não aberta; `gh` CLI indisponível no ambiente atual — abrir via interface web.
- Após merge do rename em `main`, branch pode ser descartada e a próxima frente parte de `main` limpa.

# Stable decisions

- `DOCKER_PREFLIGHT` é obrigatório antes de execução prática dependente de Docker; modo padrão permanece leve.
- O Codex opera container-first via `./scripts/dev-codex.sh`, separado do serviço `synapse-os`.
- Branch Sync Gate usa `./scripts/branch-sync-check.sh` para detectar drift; `./scripts/branch-sync-update.sh` apenas com worktree limpa e sem conflito detectável.
- `memory.md` guarda memória durável; `PENDING_LOG.md` e `ERROR_LOG.md` guardam detalhe operacional da sessão.
- `CodexCLIAdapter` é o primeiro adapter real integrado; timeout, return code não zero e bloqueios de autenticação são classificados como bloqueios operacionais externos.
- Os artefatos operacionais padrão em `.synapse-os/` devem permanecer fora do versionamento.
- O smoke autenticado do Codex (`401 Unauthorized`) permanece classificado como bloqueio operacional externo, não requisito de produto.

# Active fronts

- `chore/rename-to-synapseos`: commit concluído, PR pendente de abertura e merge em `main`.
- Nenhuma feature de produto aberta no baseline atual.

# Open decisions

- `G-11` permanece como residual real apenas no bucket `remote_multi_host_auth` — explicitamente adiado até demanda concreta.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatório.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisão estável com snapshot local ou log de conversa.
- `memory.md` e `PENDING_LOG.md` ficam rapidamente obsoletos quando merges e PRs mudam o estado real do repositório sem consolidação de handoff.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` não é seguro com worktree suja, mesmo quando o drift parece pequeno.
- Smoke real do Codex sem credencial válida falha por autenticação mesmo com launcher/container saudável.

# Next recommended steps

1. Abrir PR `claude/rename-to-synapseos-RxaIg → main` via interface web e mergear.
2. Executar `technical-triage` em branch limpa a partir de `main` para eleger a próxima feature.
3. Criar SPEC da feature eleita com `spec-editor`.
4. Manter `remote_multi_host_auth` explicitamente adiado; não reabrir F46 sem SPEC própria aprovada.

# Last handoff summary

- **Read before acting:** releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `git status`.
- **Current state:** `main` incorpora F01–F48 + rename chore pendente de PR. Branch `claude/rename-to-synapseos-RxaIg` tem 1 commit à frente, limpa, pronta para PR.
- **Open points:** abrir e mergear PR do rename; depois escolher única próxima feature via `technical-triage`.
- **Recommended next front:** após PR do rename mergeada → `technical-triage` → `spec-editor` para nova feature.
