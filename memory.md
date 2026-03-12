# Current project state

## Global project state

- AIgnt OS continua como meta-orquestrador CLI-first; o AIgnt-Synapse-Flow segue como a engine propria de pipeline do projeto.
- A baseline operacional atual combina `DOCKER_PREFLIGHT` leve por padrao, fluxo container-first para o Codex, Branch Sync Gate e separacao entre memoria duravel (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- A governanca de prompts dos agents segue formato contextual explicito, com contexto, leituras obrigatorias, objetivo, escopo, nao-faca, criterios de aceite e formato de entrega.
- O MVP de produto agora chega ate `DOCUMENT`: a F10 adicionou `RUN_REPORT.md` por run e o primeiro adapter real via `CodexCLIAdapter`.
- A F13 introduziu a primeira saida enriquecida com Rich em `src/`, mantendo o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS e limitando o recorte a `aignt runtime status`.
- A F14 adicionou observabilidade CLI-first sobre runs persistidas com `aignt runs list` e `aignt runs show <run_id>`, reaproveitando `RunRepository` e `ArtifactStore` sem abrir TUI.
- A fila oficial da etapa seguinte foi definida pelo cenario misto e documentada em `docs/architecture/PHASE_2_ROADMAP.md`: `F15 -> F16 -> F21 -> F18 -> F19 -> F20 -> F17 -> F22`.
- Uma proposta de guardrails pre-etapa-2 sobre input, secrets, rate limiting e audit trail foi avaliada e nao virou nova frente autonoma; por ora, so um endurecimento curto de mascaramento de secrets em campos `_clean` segue como candidato excepcional.
- A `F15-public-run-submission` foi concluida e mergeada em `main`: a CLI agora expõe `aignt runs submit <spec_path>` com `--mode auto|sync|async` e `--stop-at`, reaproveitando o `RunDispatchService` interno sem alterar schema nem abrir nova service layer.

## Local snapshot

- `main` local esta sincronizada com `origin/main` apos o merge da PR `#43` da `F15-public-run-submission`.
- A F15 esta concluida em `main`; a worktree atual esta suja apenas com a chore documental separada da etapa 2.
- O foco imediato nao e mais fechar a F15, e sim consolidar a documentacao pos-merge e preparar a proxima frente (`F16`).

# Stable decisions

- `DOCKER_PREFLIGHT` continua obrigatorio antes da execucao pratica de uma feature; o modo padrao permanece leve.
- O Codex opera em fluxo container-first via `./scripts/dev-codex.sh`, separado do servico `aignt-os`, onde o AIgnt-Synapse-Flow roda como engine propria de pipeline do AIgnt OS.
- A Branch Sync Gate usa `./scripts/branch-sync-check.sh` para detectar drift e `./scripts/branch-sync-update.sh` apenas quando a worktree estiver limpa e segura para atualizacao.
- `memory.md` guarda memoria duravel e reaproveitavel; `PENDING_LOG.md` e `ERROR_LOG.md` guardam detalhe operacional da sessao.
- O `memory-curator` pode ser acionado por `$memory-curator encerrar conversa` ou `$memory-curator close session` para atualizar `memory.md` e gerar handoff de encerramento.
- Com `network-access = true`, `git push` e `gh pr create` devem ser tentados primeiro no sandbox; fallback fora do sandbox fica restrito a falha real de rede ou sandbox.
- O `CodexCLIAdapter` permanece o primeiro adapter real integrado; a F12 fixou classificacao operacional explicita para timeout, return code nao zero e bloqueios de launcher/container/autenticacao sem reabrir a pipeline.
- A avaliacao de ADR pos-F12 concluiu que o hardening operacional do Codex e a chore de handoff estendem decisoes ja cobertas por ADR-004, ADR-011 e ADR-012; nao ha ADR nova nem atualizacao pendente por ora.
- Os artefatos operacionais padrao em `.aignt-os/` devem permanecer fora do versionamento.

# Active fronts

- Nenhuma nova frente de produto esta aberta neste momento.
- A frente ativa no momento e documental: consolidar o estado pos-F15 nas fontes de verdade da etapa 2.
- Nao ha frente autonoma extra antes da etapa 2; os guardrails propostos seguem reabsorvidos em `F15`/`F21`, salvo necessidade real de mascaramento de secrets em observabilidade.

# Open decisions

- A sequencia da etapa 2 ja foi decidida; a decisao imediata em aberto passa a ser quando abrir a SPEC da `F16-run-detail-expansion` apos a chore documental.
- Decidir depois do fechamento da F15 se o follow-up de mascaramento de secrets precisa virar frente propria curta ou se pode esperar a `F21`.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatorio; por ora o `401 Unauthorized` ficou classificado como bloqueio operacional externo e nao como requisito de produto.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisao estavel com snapshot local ou log de conversa.
- `memory.md` e `PENDING_LOG.md` ficam rapidamente obsoletos quando merges e PRs mudam o estado real do repositório e o handoff nao e consolidado em seguida.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` nao e seguro com worktree suja, mesmo quando o drift contra `main` parece pequeno.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.
- Smoke real do Codex sem credencial valida falha por autenticacao (`401 Unauthorized`) mesmo com launcher/container saudavel; isso deve ser tratado como bloqueio operacional externo.

# Next recommended steps

- Manter `docs/architecture/PHASE_2_ROADMAP.md`, `WORKTREE_FEATURES.md`, `README.md`, `memory.md`, `PENDING_LOG.md` e `.github/copilot-instructions.md` coerentes entre si.
- Fechar a chore documental da etapa 2 (`README.md`, roadmap, handoff e contexto operacional) agora que a F15 ja esta mergeada.
- Nao abrir features paralelas de hardening pre-etapa-2; se surgir risco concreto depois da F15, limitar o recorte a mascaramento de secrets em observabilidade.
- Quando a chore documental estiver mergeada, abrir a SPEC da `F16-run-detail-expansion`.
- Nao abrir `F14-tui-watch-command` por inercia; a etapa 2 prioriza caminho publico de execucao, diagnostico e onboarding.

# Last handoff summary

- Read before acting: releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `ERROR_LOG.md`, `git status` e `git diff --stat`.
- Current state: a `F15-public-run-submission` foi mergeada em `main`; a documentacao da etapa 2 ainda precisa ser atualizada para refletir esse novo baseline.
- Open points: fechar a chore documental pos-F15 e decidir se ha follow-up curto de mascaramento de secrets antes da `F16`.
- Recommended next front: concluir a chore documental; a proxima frente de produto continua sendo `F16-run-detail-expansion`.
