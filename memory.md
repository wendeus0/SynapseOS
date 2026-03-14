# Current project state

## Global project state

- AIgnt OS continua como meta-orquestrador CLI-first; o AIgnt-Synapse-Flow segue como a engine propria de pipeline do projeto.
- A baseline operacional atual combina `DOCKER_PREFLIGHT` leve por padrao, fluxo container-first para o Codex, Branch Sync Gate e separacao entre memoria duravel (`memory.md`) e log operacional (`PENDING_LOG.md` e `ERROR_LOG.md`).
- A governanca de prompts dos agents segue formato contextual explicito, com contexto, leituras obrigatorias, objetivo, escopo, nao-faca, criterios de aceite e formato de entrega.
- O MVP de produto agora chega ate `DOCUMENT`: a F10 adicionou `RUN_REPORT.md` por run e o primeiro adapter real via `CodexCLIAdapter`.
- A F13 introduziu a primeira saida enriquecida com Rich em `src/`, mantendo o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS e limitando o recorte a `aignt runtime status`.
- A F14 adicionou observabilidade CLI-first sobre runs persistidas com `aignt runs list` e `aignt runs show <run_id>`, reaproveitando `RunRepository` e `ArtifactStore` sem abrir TUI.
- A etapa 2 documentada em `docs/architecture/PHASE_2_ROADMAP.md` foi concluida em `main`: o baseline atual ja consolidou `F15 -> F16 -> F21 -> F18 -> F19 -> F20 -> F17 -> F22` como release tecnica coerente.
- O baseline atual tambem ja incorporou a primeira onda de guardrails pos-release com `F23 -> F27`: sanitizacao de superficies publicas, boundary de workspace/artifacts, AST guard para artifacts Python, provenance minima por run e limite local de concorrencia no adapter layer.
- A `F15-public-run-submission` foi concluida e mergeada em `main`: a CLI agora expõe `aignt runs submit <spec_path>` com `--mode auto|sync|async` e `--stop-at`, reaproveitando o `RunDispatchService` interno sem alterar schema nem abrir nova service layer.
- A `F17-artifact-preview` ja foi mergeada em `main`, adicionando preview textual controlado de `RUN_REPORT.md` e `clean_output` por step em `aignt runs show <run_id> --preview <target>`.
- A `F22-release-readiness` ja foi mergeada em `main`, fechando a etapa 2 com `CHANGELOG.md`, release notes versionada e README alinhado ao boundary entre quickstart `sync-first` e artifact preview.
- `main` atual tambem ja incorpora `F23-security-sanitization-foundation`, `F24-workspace-boundary-hardening`, `F25-generated-artifact-ast-guard`, `F26-run-provenance-integrity` e `F27-adapter-concurrency-guard`, com merges `#56` a `#60`.

## Local snapshot

- `main` local permanece sincronizada com `origin/main`, sem diff aberto no baseline usado para o handoff atual.
- A limpeza operacional pos-`F37` confirmou que o problema imediato nao era gap de MVP nem de baseline em `main`, mas drift local numa branch antiga de `F39` reutilizada para drafts pos-MVP.
- O estado misto foi preservado em `origin/archive/2026-03-13-f39-drift-snapshot`.
- As merges de `F41-dashboard-artifacts-explorer`, `F43-runtime-robustness`, `F44-auth-backend-abstraction`, `F45-tui-performance-optimization` e `F47-advanced-rbac` ja estao absorvidas em `main`.
- `main` atual tambem ja incorpora `F42-tui-filters` pela PR `#86` e `F40-local-cancellation` pela PR `#87`, consolidando filtros no dashboard TUI e cancelamento local/gracioso de runs.
- O recorte ainda transversal restante fora da fila ativa fica concentrado em `F46`, testes de lifecycle e docs especulativos de roadmap longo; `F40` e `F42` deixaram de ser backlog pendente.
- O baseline atual ja incorpora `F15-public-run-submission`, `F16-run-detail-expansion`, `F21-cli-error-model-and-exit-codes`, `F18-canonical-happy-path`, `F19-environment-doctor`, `F20-public-onboarding`, `F17-artifact-preview`, `F22-release-readiness` e a sequencia `F23 -> F27`.
- O baseline atual tambem ja incorpora `F28-adapter-circuit-breaker`, `F29-auth-rbac-foundation` e `F30-auth-registry-cli`, com `aignt auth init|issue|disable` e o alinhamento de `docs/IDEAS.md`/README ao estado pos-F30.
- A release tecnica da etapa 2 e a primeira trilha de guardrails ja estao refletidas no codigo e na superficie publica da CLI; a baseline tambem foi reestabilizada apos a PR `#66`, com `repo-checks` novamente verde.
- O baseline atual agora tambem incorpora `F31-g11-remote-auth-decomposition`, `F32-runtime-resident-principal-binding`, `F34-async-submit-runtime-ownership`, `F35-worker-runtime-ownership-filter` e `F36-worker-owner-skip-observability`.
- Com isso, o baseline fecha o recorte local de `resident_transport_auth`: binding do principal do runtime, gate de ownership no submit assincrono, filtro de ownership no worker e observabilidade local de skips incompatíveis.
- O baseline atual tambem incorpora `F41`, `F43`, `F44`, `F45` e `F47`: dashboard TUI com explorer de artifacts, robustez de timeout/retry, abstracao local de `AuthProvider`, buffering de logs na TUI e RBAC local por role.

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

- Nao ha frente de produto aberta no baseline atual.
- A frente doc-only ativa no momento e `chore-post-f40-f42-baseline-sync`, restrita a consolidar o handoff do baseline atual apos as merges de `F42` e `F40`.
- Nao ha draft coerente ainda pendente de merge entre `F41`, `F43`, `F44`, `F45` e `F47`; essas frentes ja foram absorvidas em `main`.
- Nao ha frente de implementacao de transporte remoto, socket ou auth distribuida em andamento no baseline atual.

# Open decisions

- O backlog de guardrails ficou com `G-11` como residual real apenas no bucket `remote_multi_host_auth`.
- O recorte local de auth agora inclui `F29`, `F30`, `F44` e `F47`, enquanto `resident_transport_auth` foi absorvido por `F32`, `F34`, `F35` e `F36`; nao ha decisao de produto pendente nesses buckets sem reabrir transporte novo.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatorio; por ora o `401 Unauthorized` ficou classificado como bloqueio operacional externo e nao como requisito de produto.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisao estavel com snapshot local ou log de conversa.
- `memory.md` e `PENDING_LOG.md` ficam rapidamente obsoletos quando merges e PRs mudam o estado real do repositório e o handoff nao e consolidado em seguida.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` nao e seguro com worktree suja, mesmo quando o drift contra `main` parece pequeno.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.
- Smoke real do Codex sem credencial valida falha por autenticacao (`401 Unauthorized`) mesmo com launcher/container saudavel; isso deve ser tratado como bloqueio operacional externo.

# Next recommended steps

- Fechar a `chore-post-f40-f42-baseline-sync` e, em seguida, rodar nova `technical-triage` em branch limpa a partir de `main` para escolher uma unica frente ativa.
- Nao reabrir a branch historica de `F39`; usar `draft/*` apenas como estacionamento e extrair dali somente quando houver prioridade aprovada.
- Manter `remote_multi_host_auth` explicitamente adiado e evitar reabrir follow-up local/residente de auth, porque esse recorte ja foi absorvido por `F29`, `F30`, `F44`, `F47`, `F32`, `F34`, `F35` e `F36`.

# Last handoff summary

- Read before acting: releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `ERROR_LOG.md`, `git status` e `git diff --stat`.
- Current state: `main` ja incorpora `F17`, `F22`, `F23 -> F40`, `F41`, `F42`, `F43`, `F44`, `F45` e `F47`; a baseline operacional segue verde e os recortes pendentes voltam a ser escolhidos por triagem a partir de `main`.
- Open points: concluir esta chore doc-only e depois escolher uma unica proxima frente a partir de `main`.
- Recommended next front: nova `technical-triage` em branch limpa depois do merge da `chore-post-f40-f42-baseline-sync`.
