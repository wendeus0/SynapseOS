# Current project state

## Global project state

- AIgnt OS continua como meta-orquestrador CLI-first; o AIgnt-Synapse-Flow segue como a engine propria de pipeline do projeto.
- A baseline operacional atual combina `DOCKER_PREFLIGHT` leve por padrao, fluxo container-first para o Codex, Branch Sync Gate e separacao entre memoria duravel (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- A governanca de prompts dos agents segue formato contextual explicito, com contexto, leituras obrigatorias, objetivo, escopo, nao-faca, criterios de aceite e formato de entrega.

## Local snapshot

- A frente ativa esta na worktree `feature/f08-worker-runtime-dual`, alinhada com `origin/main` antes do delta local.
- A F08 adiciona dispatch interno `sync`/`async`/`auto`, worker leve consumindo runs pendentes, suporte a `stop_at=SPEC_VALIDATION`, checklist da feature e ignorar `.aignt-os/` no Git.
- Os gates locais mais recentes da F08 fecharam verdes: `commit-check --no-sync --skip-docker --skip-security`, `DOCKER_PREFLIGHT` real com `--full-runtime`, container `aignt-os` em estado `healthy`, e suite completa com `223` testes verdes.

# Stable decisions

- `DOCKER_PREFLIGHT` continua obrigatorio antes da execucao pratica de uma feature; o modo padrao permanece leve.
- O Codex opera em fluxo container-first via `./scripts/dev-codex.sh`, separado do servico `aignt-os`, onde o AIgnt-Synapse-Flow roda como engine propria de pipeline do AIgnt OS.
- A Branch Sync Gate usa `./scripts/branch-sync-check.sh` para detectar drift e `./scripts/branch-sync-update.sh` apenas quando a worktree estiver limpa e segura para atualizacao.
- `memory.md` guarda memoria duravel e reaproveitavel; `PENDING_LOG.md` e `ERROR_LOG.md` guardam detalhe operacional da sessao.
- O `memory-curator` pode ser acionado por `$memory-curator encerrar conversa` ou `$memory-curator close session` para atualizar `memory.md` e gerar handoff de encerramento.
- Com `network-access = true`, `git push` e `gh pr create` devem ser tentados primeiro no sandbox; fallback fora do sandbox fica restrito a falha real de rede ou sandbox.
- Na F08, o runtime foreground passa a poder hospedar um worker leve do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, sem nova CLI publica de runs.
- Os artefatos operacionais padrao em `.aignt-os/` devem permanecer fora do versionamento.

# Active fronts

- Fechar a F08 no fluxo Git com `security-review`, commit, push e PR.
- Abrir a F09 logo apos o fechamento da F08, mantendo o recorte em supervisor MVP com retry deterministico, reroute simples e falha terminal.

# Open decisions

- Confirmar na F10 qual adapter real sera priorizado no happy path final; default atual continua sendo Codex CLI.
- Decidir depois do merge da F08 se vale endurecer o tratamento de falhas amplas do worker alem do recorte MVP atual.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisao estavel com snapshot local ou log de conversa.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` nao e seguro com worktree suja, mesmo quando o drift contra `main` parece pequeno.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.

# Next recommended steps

- Concluir o `security-review` da F08 e fechar commit/push/PR da branch `feature/f08-worker-runtime-dual`.
- Depois do merge da F08, abrir a F09 com `spec-editor` → `test-red` → `green-refactor`.
- Deixar limpeza ampla de logs/docs antigos fora do caminho critico ate o MVP fechar.

# Last handoff summary

- Read before acting: releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `ERROR_LOG.md`, `git status` e `git diff --stat`.
- Current state: a F08 esta implementada e validada localmente, incluindo worker leve, dispatch interno e `DOCKER_PREFLIGHT` real com runtime saudavel.
- Open points: concluir o parecer de seguranca da F08, fechar commit/PR e depois abrir a F09.
- Recommended next front: terminar o fechamento Git da F08 e so entao iniciar a frente do supervisor MVP.
