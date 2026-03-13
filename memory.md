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
- O baseline atual ja incorpora `F15-public-run-submission`, `F16-run-detail-expansion`, `F21-cli-error-model-and-exit-codes`, `F18-canonical-happy-path`, `F19-environment-doctor`, `F20-public-onboarding`, `F17-artifact-preview`, `F22-release-readiness` e a sequencia `F23 -> F27`.
- O baseline atual tambem ja incorpora `F28-adapter-circuit-breaker`, `F29-auth-rbac-foundation` e `F30-auth-registry-cli`, com `aignt auth init|issue|disable` e o alinhamento de `docs/IDEAS.md`/README ao estado pos-F30.
- A release tecnica da etapa 2 e a primeira trilha de guardrails ja estao refletidas no codigo e na superficie publica da CLI; a baseline tambem foi reestabilizada apos a PR `#66`, com `repo-checks` novamente verde.
- A branch de trabalho atual abriu a `F31-g11-remote-auth-decomposition` como frente doc-only para fechar a ambiguidade do residual de `G-11` antes de qualquer nova implementacao de produto.

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

- A frente ativa agora e a `F31-g11-remote-auth-decomposition`, uma frente doc-only de SPEC/backlog.
- Nao ha frente de implementacao de transporte remoto, socket ou auth distribuida em andamento no baseline atual.

# Open decisions

- O backlog de guardrails ficou com `G-11` como residual real, mas ele agora esta sendo decomposto em `local_cli_auth`, `resident_transport_auth` e `remote_multi_host_auth`.
- A proxima decisao codificavel passa a ser qual sera a SPEC pequena derivada do bucket `resident_transport_auth`, nao uma implementacao direta de auth remota.
- Decidir em momento futuro se o smoke autenticado do Codex deve virar gate obrigatorio; por ora o `401 Unauthorized` ficou classificado como bloqueio operacional externo e nao como requisito de produto.

# Recurrent pitfalls

- `memory.md` perde valor quando mistura decisao estavel com snapshot local ou log de conversa.
- `memory.md` e `PENDING_LOG.md` ficam rapidamente obsoletos quando merges e PRs mudam o estado real do repositório e o handoff nao e consolidado em seguida.
- `uv` pode falhar no sandbox por cache fora da workspace ou indisponibilidade de rede.
- `branch-sync-update` nao e seguro com worktree suja, mesmo quando o drift contra `main` parece pequeno.
- Subir `codex-dev` manualmente em paralelo ao launcher pode causar corrida operacional.
- Smoke real do Codex sem credencial valida falha por autenticacao (`401 Unauthorized`) mesmo com launcher/container saudavel; isso deve ser tratado como bloqueio operacional externo.

# Next recommended steps

- Fechar a `F31` com SPEC validada, backlog/documentacao alinhados e teste de documentacao travando o novo estado de `G-11`.
- So depois abrir a primeira SPEC de codigo derivada de `resident_transport_auth`, mantendo `remote_multi_host_auth` explicitamente adiado.
- Evitar reabrir follow-up local de auth, porque esse recorte ja foi absorvido por `F29` e `F30`.

# Last handoff summary

- Read before acting: releia `AGENTS.md`, `CONTEXT.md`, `memory.md`, `PENDING_LOG.md`, `ERROR_LOG.md`, `git status` e `git diff --stat`.
- Current state: `main` ja incorpora `F17`, `F22`, `F23 -> F30` e a baseline operacional voltou a ficar verde apos a `#66`.
- Open points: concluir a decomposicao documental de `G-11` e transformar apenas o bucket `resident_transport_auth` no proximo candidato de SPEC pequena.
- Recommended next front: fechar a `F31` e, depois disso, abrir a primeira SPEC de codigo derivada do residual residente/local de `G-11`.
