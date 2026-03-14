# Current project state

## Global project state

- SynapseOS é o meta-orquestrador CLI-first; o Synapse-Flow é a engine própria de pipeline do projeto.
- A baseline operacional combina `DOCKER_PREFLIGHT` leve por padrão, fluxo container-first para o Codex, Branch Sync Gate e separação entre memória durável (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- O MVP chega até `DOCUMENT`: `RUN_REPORT.md` por run, `CodexCLIAdapter` como primeiro adapter real, CLI enriquecida com Rich, observabilidade CLI de runs e TUI dashboard com explorer, filtros, log viewer e cancelamento local.
- A etapa 2 está completa em `main` (F15–F22); a primeira onda de guardrails também está completa (F23–F27).
- O baseline incorpora F28–F36 (circuit breaker, RBAC foundation, auth registry CLI, principal binding, ownership filter/worker, skip observability) e F40–F47 (cancelamento local, dashboard TUI, robustez de runtime, auth abstraction, TUI perf, RBAC por role).
- `F48-spec-validation-gate` mergeada em `main` via PR #91: o Synapse-Flow bloqueia execução quando a SPEC não passa na validação antes de `PLAN`.
- O rename cosmético `AIgnt OS → SynapseOS` foi concluído e mergeado em `main` via PR #94 (commit `bc9ceab`): pacote Python (`synapse_os`), env prefix (`SYNAPSE_OS_`), Docker (`synapse-os`), pipeline engine (`Synapse-Flow`), runtime dirs (`.synapse-os/`), 254 arquivos.
- `F49-pipeline-full-flow-integration` está concluída na branch `claude/F49-pipeline-full-flow-integration-RxaIg`: adiciona `tests/pipeline/test_full_flow.py` com 12 testes de integração do `PipelineEngine` cobrindo os estados finais do Synapse-Flow (REVIEW, SECURITY, DOCUMENT, COMPLETE) + REPORT.md de fechamento. Zero mudanças em código de produção.

## Local snapshot

- Branch atual: `claude/F49-pipeline-full-flow-integration-RxaIg` — 3 commits à frente de `main`, working tree limpa.
- PR F49 pendente de abertura e merge via interface web do GitHub (`main` protegida, `gh` CLI indisponível no ambiente sandbox).
- Após merge da PR F49, `main` incorporará F01–F49 e a próxima frente parte de `main` limpa.

# Stable decisions

- `DOCKER_PREFLIGHT` é obrigatório antes de execução prática dependente de Docker; modo padrão permanece leve.
- O Codex opera container-first via `./scripts/dev-codex.sh`, separado do serviço `synapse-os`.
- Branch Sync Gate usa `./scripts/branch-sync-check.sh` para detectar drift; `./scripts/branch-sync-update.sh` apenas com worktree limpa e sem conflito detectável.
- `memory.md` guarda memória durável; `PENDING_LOG.md` e `ERROR_LOG.md` guardam detalhe operacional da sessão.
- `CodexCLIAdapter` é o primeiro adapter real integrado; timeout, return code não zero e bloqueios de autenticação são classificados como bloqueios operacionais externos.
- Os artefatos operacionais padrão em `.synapse-os/` devem permanecer fora do versionamento.
- O smoke autenticado do Codex (`401 Unauthorized`) permanece classificado como bloqueio operacional externo, não requisito de produto.
- Sempre usar `python -m pytest` e `python -m mypy` (não wrappers da `.venv`) — padrão endurecido contra wrappers quebrados.

# Active fronts

- `F49-pipeline-full-flow-integration`: 3 commits commitados e pushed na branch `claude/F49-pipeline-full-flow-integration-RxaIg`; PR pendente de merge via web. Nenhuma pendência técnica — só o merge.

# Open decisions

- `G-11` permanece como residual real apenas no bucket `remote_multi_host_auth` — explicitamente adiado até demanda concreta.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatório.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisão estável com snapshot local ou log de conversa.
- `memory.md` e `PENDING_LOG.md` ficam rapidamente obsoletos quando merges e PRs mudam o estado real do repositório sem consolidação de handoff.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` não é seguro com worktree suja, mesmo quando o drift parece pequeno.
- Smoke real do Codex sem credencial válida falha por autenticação mesmo com launcher/container saudável.
- Merge direto para `main` via `git push` resulta em 403 — `main` é protegida; sempre usar PR via web ou API quando `gh` não estiver disponível.

# Next recommended steps

1. Mergear PR F49 via interface web: `https://github.com/wendeus0/aignt-os/compare/main...claude/F49-pipeline-full-flow-integration-RxaIg`
2. Executar `technical-triage` em `main` limpa pós-merge para eleger a próxima feature (F50).
3. Criar SPEC da feature eleita com `spec-editor`.
4. Manter `remote_multi_host_auth` explicitamente adiado; não reabrir F46 sem SPEC própria aprovada.

# Last handoff summary

- **Read before acting:** releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `git status`.
- **Current state:** `main` incorpora F01–F48 + rename (PR #94). Branch `claude/F49-pipeline-full-flow-integration-RxaIg` tem 3 commits à frente, limpa, pronta para PR. memory.md atualizado pós-F49.
- **Open points:** única pendência técnica — merge da PR F49 via web. Sem conflitos, sem drift, fast-forward limpo.
- **Recommended next front:** após merge da PR F49 → `technical-triage` em `main` para eleger F50.
