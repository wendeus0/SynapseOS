# PENDING_LOG

## Decisões incorporadas recentemente

- Em 2026-03-13, `origin/main` absorveu as merges de `F41-dashboard-artifacts-explorer` (`#80`), `F44-auth-backend-abstraction` (`#81`), `F47-advanced-rbac` (`#82`), `F43-runtime-robustness` (`#83`) e `F45-tui-performance-optimization` (`#84`), consolidando a TUI local, a robustez basica de timeout/retry e o baseline atual de auth local.
- Com essas merges, `main` passou a refletir explorer de artifacts na TUI, buffering de logs, timeout global por step, retry simples para falhas transientes, abstracao local de `AuthProvider` e RBAC local com `viewer`/`operator`/`admin`.
- O drift remanescente deixou de ser funcional e passou a ser documental: `memory.md`, `PENDING_LOG.md`, `docs/IDEAS.md`, `README.md` e `CHANGELOG.md` ficaram atrasados em relacao ao baseline real pos-`F47`.
- A frente ativa imediata passa a ser a chore doc-only `chore-post-f47-baseline-handoff-sync`, para consolidar o handoff do baseline atual antes da proxima decisao de produto.
- A proxima decisao de produto volta a ficar bloqueada ate essa chore fechar e uma nova `technical-triage` escolher uma unica frente a partir de `main`.

- Em 2026-03-13, a triagem pos-`F37` confirmou que `origin/main` ja cobre o MVP, a etapa 2 e o handoff doc-only pos-`F36`; o bloqueio real estava na branch local `feature/f39-persistence-path-root-hardening`, que havia virado agregador de drafts fora de escopo.
- O estado misto foi preservado em `origin/archive/2026-03-13-f39-drift-snapshot`, e os recortes determinísticos foram separados em `origin/draft/f41-dashboard-artifacts-explorer`, `origin/draft/f43-runtime-robustness`, `origin/draft/f44-auth-backend-abstraction`, `origin/draft/f45-tui-performance-optimization` e `origin/draft/f47-advanced-rbac`.
- Os itens transversais que ainda nao cabem numa unica frente sem inventar codigo novo (`F40`, `F42`, `F46`, testes de lifecycle e docs de roadmap de longo prazo`) ficaram somente no archive branch, sem virar fila ativa nem PR aberta.
- Com isso, a frente ativa imediata deixa de ser `F37` e passa a ser nenhuma: a linha principal volta a partir de `main`, e a proxima decisao de produto fica bloqueada ate nova `technical-triage` em branch limpa.

- Em 2026-03-13, a `F34-async-submit-runtime-ownership` foi mergeada em `main` pela PR `#70`, fazendo `runs submit` autenticado aceitar dispatch resolvido para `async` apenas quando o runtime residente pertence ao mesmo principal, preservando fallback legado sem `started_by`.
- Em 2026-03-13, a `F35-worker-runtime-ownership-filter` foi mergeada em `main` pela PR `#71`, fazendo o worker do runtime residente consumir apenas runs compativeis com o principal que iniciou o runtime, sem falhar nem lockar runs incompatíveis.
- Em 2026-03-13, a `F36-worker-owner-skip-observability` foi mergeada em `main` pela PR `#72`, tornando auditavel o skip do worker com evento `runtime_owner_skip` nas runs incompatíveis e mantendo o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS.
- Com `F32`, `F34`, `F35` e `F36`, o bucket local de `resident_transport_auth` deixa de ser backlog funcional aberto e passa a ser baseline absorvido; o residual real de `G-11` fica restrito a operacao remota/multi-host.
- A frente ativa imediata deixa de ser triagem de produto e passa a ser a chore doc-only `F37-post-f36-g11-sync`, para alinhar handoff e backlog ao estado pos-`#72` antes da proxima decisao de produto.
- A proxima decisao de produto fica bloqueada ate `PENDING_LOG.md`, `memory.md` e `docs/IDEAS.md` refletirem o baseline real pos-`F36`.

- Em 2026-03-13, a `F32-runtime-resident-principal-binding` foi mergeada em `main` pela PR `#68`, entregando o primeiro slice concreto do bucket `resident_transport_auth` sem abrir socket, IPC ou operacao remota.
- A `F32` persistiu `started_by` no estado do runtime quando auth local esta habilitada, passou a exibir esse binding em `aignt runtime status` e endureceu `aignt runtime stop` contra operador diferente quando o binding existe.
- Com a `F32`, o residual de `G-11` deixa de ser apenas fundacao local absorvida versus backlog futuro: o bucket `resident_transport_auth` ja tem um primeiro slice entregue, enquanto operacao remota/multi-host continua explicitamente adiada.
- A frente ativa imediata deixou de ser feature de produto e passou a ser chore doc-only de handoff: `F33-post-f32-handoff-sync`, para alinhar memoria operacional e backlog ao estado pos-`#68` antes da proxima triagem.
- A proxima decisao de produto fica bloqueada ate `PENDING_LOG.md`, `ERROR_LOG.md`, `memory.md` e `docs/IDEAS.md` refletirem o baseline real pos-`F32`.

- Em 2026-03-13, a baseline voltou a ficar estavel apos a merge da PR `#66`, com `repo-checks` e `security-review` verdes na checagem remota e `ruff format --check .` restaurado como gate verde local.
- Com a baseline estabilizada, a frente ativa deixou de ser operacional e voltou a ser backlog de produto: `F31-g11-remote-auth-decomposition`.
- A `F31` foi aberta como frente doc-only para decompor formalmente o residual de `G-11` em `local_cli_auth` ja absorvido, `resident_transport_auth` ainda pendente e `remote_multi_host_auth` explicitamente adiado.
- O proximo trabalho de codigo fica bloqueado ate essa decomposicao documental fechar uma SPEC pequena e verificavel para o bucket `resident_transport_auth`.

- Em 2026-03-13, a `F30-auth-registry-cli` foi mergeada em `main` pela PR `#65`, adicionando `aignt auth init|issue|disable`, `token_id` no registry local e alinhamento de `docs/IDEAS.md`/README ao baseline pos-F30.
- A `F30` fechou o follow-up local de auth iniciado pela `F29`; o residual real de `G-11` ficou reduzido ao recorte grande de operacao remota/socket, explicitamente adiado.
- O fechamento Git da `F30` exigiu merge explicito porque o job `repo-checks` permaneceu vermelho por `ruff format --check .` em 6 arquivos preexistentes fora do diff funcional da feature.
- Com isso, a proxima frente logica deixou de ser backlog de produto e passou a ser estabilizacao da baseline: restaurar `repo-checks` e sincronizar o handoff pos-F30 antes de abrir nova SPEC.

- Em 2026-03-12, a `F28-adapter-circuit-breaker` foi mergeada em `main` pela PR `#62`, absorvendo `G-09` com breaker persistido local para o `CodexCLIAdapter` sem reabrir SQLite, auth remota ou CLI publica.
- Em 2026-03-12, a `F29-auth-rbac-foundation` foi mergeada em `main` pela PR `#63`, endurecendo `runs submit` e `runtime start|run|stop` com auth opt-in local, registry privado por hash SHA-256 e reuso de `initiated_by` para provenance autenticada.
- Com `F28` e `F29`, a triagem pos-`F27` deixou de ser `G-09` versus `G-11`: o backlog imediato agora precisa distinguir entre follow-up residual de auth (`socket`, rotacao/provisionamento e operacao remota`) e outras frentes fora da `IDEA-001`.

- Em 2026-03-12, o handoff operacional foi realinhado ao baseline real pós-`F27`: `main` já incorpora `F23-security-sanitization-foundation`, `F24-workspace-boundary-hardening`, `F25-generated-artifact-ast-guard`, `F26-run-provenance-integrity` e `F27-adapter-concurrency-guard`, via merges `#56` a `#60`.
- Com esse realinhamento, a “primeira SPEC pós-`F22`” deixou de ser pendência atual: a etapa 2 e a primeira onda de guardrails já foram concluídas em `main`, e a próxima decisão passa a ser a primeira SPEC pós-`F27`.
- O backlog remanescente da `IDEA-001` ficou reduzido principalmente a `G-09` (circuit breaker para adapters) e `G-11` (autenticação/autorização), com `G-09` como menor recorte técnico natural para a próxima triagem.

- Em 2026-03-12, o baseline documental foi realinhado ao estado real do repositório: `main` já incorpora `F17-artifact-preview` e `F22-release-readiness`, fechando a etapa 2 no código, na CLI pública e na release técnica.
- A `F17-artifact-preview` foi mergeada em `main`, consolidando `aignt runs show <run_id> --preview report` e `--preview <STEP_STATE>.clean` com leitura textual truncada e sem abrir leitura arbitrária do host.
- A `F22-release-readiness` foi mergeada em `main`, consolidando `CHANGELOG.md`, `docs/release/phase-2-technical-release.md`, README alinhado ao quickstart `sync-first` e boundary explícito para artifact preview.
- A próxima decisão do projeto deixou de ser fechar PRs da etapa 2 e passou a ser abrir a primeira SPEC pós-`F22`; `docs/IDEAS.md` permanece como backlog candidato, com `IDEA-001 / G-02` como menor recorte imediato se houver risco real em observabilidade pública.

- A `F13-rich-cli-output` foi concluida localmente como frente pequena de UX na CLI, sem ampliar a arquitetura: `aignt runtime status` passou a renderizar painel Rich com status e PID, mantendo `stderr` e exit code de falha no estado inconsistente.
- A F13 introduziu `src/aignt_os/cli/rendering.py` como helper minima de apresentacao e adicionou cobertura dedicada em `tests/unit/test_cli_rich_output.py` e `tests/integration/test_runtime_cli.py`.
- A validacao local da F13 fechou verde com `validate_spec_file()` da SPEC, `pytest tests/unit/test_cli_rich_output.py tests/integration/test_runtime_cli.py`, `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security` e `./scripts/security-gate.sh`.
- O recorte da F13 permaneceu deliberadamente restrito a `aignt runtime status`, sem `Textual`, sem watch mode, sem novo subcomando publico e sem necessidade de `DOCKER_PREFLIGHT`.
- A `F14-runs-observability-cli` foi concluida localmente como frente pequena de observabilidade CLI-first, adicionando `aignt runs list` e `aignt runs show <run_id>` sem abrir TUI.
- A F14 reaproveitou `RunRepository` e `ArtifactStore`, estendeu `src/aignt_os/cli/rendering.py` para listagem/detalhe de runs e manteve o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS.
- A validacao local da F14 fechou verde com `validate_spec_file()` da SPEC, `pytest` focado de CLI/persistencia, `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security` e `./scripts/security-gate.sh`.
- O recorte da F14 permaneceu deliberadamente restrito a leitura de runs persistidas: sem watch mode, sem streaming, sem Textual e sem `DOCKER_PREFLIGHT`.
- A PR `#42` da `F14-runs-observability-cli` foi mergeada em `main`, consolidando `aignt runs list` e `aignt runs show <run_id>` como superficie publica atual do projeto.
- A etapa seguinte do projeto foi definida e documentada como fila oficial em `docs/architecture/PHASE_2_ROADMAP.md`, seguindo o cenario misto: `F15 -> F16 -> F21 -> F18 -> F19 -> F20 -> F17 -> F22`.
- Uma proposta posterior de guardrails pre-etapa-2 (input, secrets, rate limiting e audit trail) foi triada e nao foi promovida a duas features autonomas; o backlog oficial preserva a etapa 2 como proxima trilha principal.
- O unico recorte excepcional aceito antes da etapa 2, se houver risco real, e mascaramento de secrets em campos `_clean` e artifacts de leitura publica; o restante deve ser absorvido em `F15` e `F21`.
- A `F15-public-run-submission` foi implementada localmente com `aignt runs submit <spec_path>`, `--mode auto|sync|async` e `--stop-at`, reaproveitando o `RunDispatchService` interno e fixando `SPEC_VALIDATION` como default operacional seguro.
- O hardening principal da F15 ficou no proprio dispatch: a SPEC e validada antes de qualquer submit, inclusive em `async`, para evitar persistencia de runs invalidas.
- A validacao local da F15 fechou verde com `validate_spec_file()` da SPEC, `pytest` focado de dispatch/runs/runtime, `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security` e `./scripts/security-gate.sh`.
- A PR `#43` da `F15-public-run-submission` foi mergeada em `main`, consolidando `aignt runs submit <spec_path>` como superficie publica atual junto de `aignt runs list/show`.
- A chore documental pos-F15 alinhou `README.md`, `WORKTREE_FEATURES.md`, `memory.md`, `PENDING_LOG.md` e `.github/copilot-instructions.md` ao baseline atual da etapa 2.
- O baseline real atual tambem ja incorpora a `F16-run-detail-expansion`, a `F21-cli-error-model-and-exit-codes` e a `F18-canonical-happy-path`: as tres frentes tem `SPEC.md` propria, notes/checklists, comportamento materializado na CLI e cobertura dedicada em testes unitarios e de integracao.
- A revalidacao focada do baseline da etapa 2 fechou verde com `uv run --no-sync python -m pytest tests/unit/test_cli_runs_rendering.py tests/integration/test_runs_submit_cli.py tests/integration/test_cli_error_model.py -q`, totalizando `12 passed`.
- O handoff operacional foi realinhado para refletir a fila remanescente correta da etapa 2: `F19 -> F20 -> F17 -> F22`.
- A `F19-environment-doctor` foi concluida e mergeada pela PR `#51`, consolidando `aignt doctor` como diagnostico local e advisory do fluxo publico atual.
- A `F20-public-onboarding` foi concluida e mergeada pela PR `#52`, consolidando o quickstart publico sync-first e o boundary entre `aignt doctor` e `repo-preflight`.
- Com a merge de `F19` e `F20`, a fila remanescente real da etapa 2 passou a ser `F17 -> F22`.
- A `F17-artifact-preview` foi concluida localmente com preview textual controlado em `aignt runs show <run_id> --preview <target>`, suportando `report` e `<STEP_STATE>.clean` sem abrir leitura arbitraria do host.
- O delta da F17 manteve o contrato de erros da F21 (`Usage error:`/`2`, `Not found:`/`3`) e limitou a leitura ao inicio do artifact, com truncamento explicito apos no maximo 40 linhas.
- A PR `#53` da `F17-artifact-preview` foi aberta contra `main`, deixando a frente pronta para revisao sem merge antecipado.
- A `F22-release-readiness` foi concluida localmente como frente documental e de validacao final, adicionando `CHANGELOG.md`, release notes versionada e boundary explicito entre quickstart sync-first e artifact preview.

- A `F10-run-report-one-real-adapter` foi concluida e mergeada em `main`, fechando o MVP inicial do AIgnt-Synapse-Flow com `DOCUMENT`, `RUN_REPORT.md` e o primeiro adapter real (`CodexCLIAdapter`).
- A `F12-codex-adapter-operational-hardening` foi concluida e mergeada pela PR `#38`, com `main` local e `origin/main` sincronizados em `ahead=0 behind=0`.
- O hardening da F12 manteve `CLIExecutionResult` como contrato de execucao e adicionou classificacao operacional explicita do Codex (`timeout`, `return_code_nonzero`, `launcher_unavailable`, `container_unavailable`, `authentication_unavailable`) sem reabrir a pipeline.
- O `DOCKER_PREFLIGHT` real e o smoke container-first do Codex foram validados; o unico bloqueio observado foi autenticacao ausente (`401 Unauthorized`), tratado como bloqueio operacional externo e nao como defeito do adapter.

- A chore `test-layout-typecheck-hardening` estabilizou a arvore `tests/` com package markers explicitos, removendo a colisao operacional entre `tests/unit/conftest.py` e `tests/integration/conftest.py`.
- O repositório agora aceita `uv run mypy src tests`, mas isso foi fechado via override explícito do `mypy` para `tests` e `tests.*`, preservando o contrato strict no pacote `src/aignt_os`.

- A `F09-supervisor-mvp` foi materializada com `SPEC.md`, `NOTES.md` e `CHECKLIST.md` proprios, mantendo o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS e limitando o recorte a supervisor deterministico, pipeline linear ate `SECURITY` e persistencia de decisoes do supervisor.
- A pipeline agora suporta `CODE_GREEN`, `REVIEW` e `SECURITY`; a state machine passou a aceitar `REVIEW -> CODE_GREEN` para rework, e o novo modulo `aignt_os.supervisor` decide entre `retry`, `reroute`, `return_to_code_green` e `fail` de forma deterministica.
- A persistencia de runs da F09 passou a registrar eventos `supervisor_decision`, e a validacao local da feature fechou verde com `233` testes passando, `ruff check`, `uv run --no-sync python -m mypy`, `./scripts/security-gate.sh` e `./scripts/commit-check.sh --skip-docker`.
- O recorte da F09 manteve `retry` e `reroute` dentro da mesma execucao da pipeline; nao houve retomada persistida entre polls do worker nem ampliacao para `DOCUMENT` ou `RUN_REPORT.md`.

- Os três documentos arquiteturais principais foram refinados para maior convergência: `SPEC_FORMAT.md` ganhou tabela de campos obrigatórios, regra H1 obrigatória documentada, valores válidos para `type`, assimetria intencional `non_goals`/`acceptance_criteria` explicada, referência ao template v2 e nova seção sobre testes de integração nos acceptance_criteria. `TDD.md` teve nomes de testes corrigidos para convenção do projeto, seção 9 de fixtures marcada com ✅/🔜, seção 10 sincronizada com estrutura real, e nova seção 13 formalizando requisito de testes de integração por categoria de feature. `SDD.md` teve estados `INIT`/`RETRYING` marcados como pós-MVP, DOCKER_PREFLIGHT reposicionado como gate lateral no diagrama, `metadata: dict` corrigido para `dict[str, Any]`, `parser_confidence` e `REQUEST.md` marcados como não implementados no MVP, e tabela de mapeamento macro ↔ estados internos adicionada na seção 5.
- A suíte de testes foi expandida de 88 → 215 testes ao longo da sessão de hardening: novos conftest.py (unit + integration), fixtures de SPEC inválidas, fixtures de CLI output realistas, test_spec_validator (4→18), test_state_machine (5→30), test_parsing_engine (9→21), test_contracts (4→17), test_config (4→12), test_happy_path (20 novos), test_failure_recovery (9 novos), test_review_rework (11 novos), test_adapter_parser_flow (10 novos de integração).
- `pytest-cov>=5.0.0` foi adicionado ao `pyproject.toml` com configuração `[tool.coverage.run]` e `[tool.coverage.report]`. Versão instalada: `7.0.0`.
- Os `acceptance_criteria` de F02, F03, F04 e F05 foram atualizados para incluir pelo menos um critério verificável somente via teste de integração, alinhando as SPECs com o novo requisito documentado em `TDD.md` seção 13 e `SPEC_FORMAT.md`.
- Fixtures novas criadas: `tests/fixtures/docker/valid_compose_config.txt`, `invalid_compose_config.txt`, `tests/fixtures/reports/expected_run_report.md`, `tests/fixtures/cli_outputs/gemini_plan.txt`, `codex_tests.txt`, `claude_review.txt`.
- Security review da branch `chore/tdd-integration-hardening` foi aprovado sem ressalvas: zero mudanças em código de produção, todos os padrões de subprocess existentes são legítimos, uso de `unicode_escape` em fixtures é controlado e sem risco de injeção.

- A correcao de follow-up da `F06-pipeline-engine-linear` reexportou `SpecValidationError` em `aignt_os.pipeline`, alinhando a API publica da engine com o teste de bloqueio por SPEC invalida e restaurando o `repo-checks` local no mesmo caminho usado pelo CI.
- A `F06-pipeline-engine-linear` passou a ter `SPEC.md` propria, `NOTES.md`, contratos tipados de pipeline (`PipelineStep`, `StepExecutionResult`, `PipelineContext`) e uma `PipelineEngine` linear em fake mode para o AIgnt-Synapse-Flow.
- O recorte da `F06-pipeline-engine-linear` ficou deliberadamente restrito a `SPEC_VALIDATION`, `PLAN` e `TEST_RED`, reutilizando `SpecValidator` e state machine ja existentes, sem persistencia, worker, supervisor ou adapters reais.
- A validacao local da `F06-pipeline-engine-linear` fechou verde com `SPEC` validada, `88` testes passando via `python -m pytest`, `ruff check`, `ruff format --check`, `mypy` e `./scripts/branch-sync-check.sh` em `ahead=0 behind=0`.
- O `security-review` do delta da `F06-pipeline-engine-linear` foi concluido sem ressalvas: a feature nao adiciona shell, subprocesso novo, Docker, workflow ou automacao operacional, e mantem a execucao de pipeline em fake mode com contexto em memoria e validacao explicita da SPEC antes de `PLAN`.

- A `F05-cli-adapter-base` passou a ter `SPEC.md` propria, `NOTES.md`, um `BaseCLIAdapter` assíncrono via `asyncio.create_subprocess_exec` e a evolucao de `CLIExecutionResult` para incluir `tool_name`, `stdout/stderr` raw/clean, `duration_ms` e `timed_out`.
- O recorte da `F05-cli-adapter-base` ficou deliberadamente restrito a contrato de execucao, subprocesso async, timeout e sanitizacao leve de ANSI, preservando o Parsing Engine da `F04` como responsavel por limpeza mais rica e extracao de artefatos antes dos hand-offs do AIgnt-Synapse-Flow.
- A validacao local da `F05-cli-adapter-base` fechou verde com `SPEC` validada, `84` testes passando via `python -m pytest`, `ruff check`, `ruff format --check`, `mypy` e `./scripts/branch-sync-check.sh` em `ahead=0 behind=0`.
- O `security-review` do delta da `F05-cli-adapter-base` foi concluido sem ressalvas: a implementacao usa `create_subprocess_exec` sem shell, preserva output bruto separado do output limpo, aplica timeout com encerramento explicito do processo e mantem a sanitizacao conservadora no adapter.

- A `F04-parsing-engine-mvp` passou a ter `SPEC.md` propria, fixtures de output ruidoso e um Parsing Engine minimo com limpeza de ANSI, extracao de blocos fenced Markdown e validacao sintatica de artefatos Python.
- O hardening final da `F04-parsing-engine-mvp` normalizou linguagem de fences para lowercase, canonizou `py` para `python`, preservou texto semantico generico ao remover apenas ruido de transporte explicito e adicionou limites fixos de tamanho/volume no parser.
- A validacao local mais recente da `F04-parsing-engine-mvp` fechou verde com `./scripts/commit-check.sh --no-sync --skip-branch-validation --skip-docker --skip-security`, incluindo `81` testes verdes, `ruff` e `mypy`.
- O `security-review` final da `F04-parsing-engine-mvp` foi reavaliado apos o hardening do parser e ficou aprovado sem ressalvas no recorte atual.
- O fluxo de PR assistido pelo agente Git passou a exigir corpo de PR via `--body-file` em vez de `--body` inline quando houver Markdown com backticks, blocos de codigo ou outros caracteres shell-sensitive, evitando corrupção da descrição publicada por expansão acidental do shell.
- A baseline MCP do `codex-dev` passou a ser segura por padrao: `.codex/config.toml` deixou de carregar `github-actions`, `sqlite` e `docker` no startup default, e o MCP oficial do GitHub passou a ser renderizado dinamicamente apenas quando houver token no ambiente.
- O fallback de `GITHUB_TOKEN` para `GITHUB_PERSONAL_ACCESS_TOKEN` ficou centralizado em `scripts/render-codex-config.sh`, tornando o launcher do Codex testavel e removendo a dependencia de symlink persistida no volume `codex-home`.
- A avaliacao operacional confirmou que o MCP de Docker deve ficar fora do baseline do `codex-dev`, porque o ambiente isolado continua sem `docker.sock`.
- `tests/unit/test_repo_automation.py` passou a cobrir o baseline seguro do MCP do Codex, a renderizacao da config efetiva com e sem token e a ausencia de `docker.sock` no `codex-dev`.
- A validacao desta frente ficou fechada com `./scripts/docker-preflight.sh`, `pytest tests/unit/test_repo_automation.py` verde, smoke do `dev-codex.sh` sem token e smoke com fallback via `GITHUB_TOKEN`.
- O `security-review` do delta MCP/Codex foi concluido com aprovacao e duas ressalvas baixas e nao bloqueantes: o helper de renderizacao aceita `--source`/`--output` arbitrarios e o fallback de `GITHUB_TOKEN` pode habilitar o MCP do GitHub em ambientes onde essa variavel ja exista por outro motivo.
- O fechamento Git desta frente foi isolado na branch `chore/codex-mcp-baseline-hardening` com commit local `89e8111 chore(repo): harden codex mcp baseline`, sem push e sem PR.
- A validação operacional de `uv sync --locked --extra dev` foi concluída com sucesso em ambiente com rede liberada.
- A validação real do job `branch-validation` em GitHub Actions foi concluída com sucesso, confirmando checkout por `github.event.pull_request.head.sha` e uso de `github.head_ref` para o nome efetivo da branch em `pull_request`.
- O fluxo local de `./scripts/commit-check.sh --no-sync` foi endurecido para executar `mypy` e `pytest` via `python -m ...`, reduzindo dependência de wrappers quebrados na `.venv`.
- A validação operacional de `./scripts/docker-preflight.sh` sem `--dry-run` foi concluída com sucesso no modo padrão leve (`compose config` + build, sem `up`) em ambiente com Docker acessível.
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
- A revalidação operacional mais recente confirmou `ruff format --check .` verde no estado atual do repositório, restaurando o gate completo de formatação sem necessidade de ajuste adicional.
- A sincronização conservadora da branch atual com `origin/main` foi revalidada com `git fetch origin main --prune`, `./scripts/branch-sync-check.sh` e `./scripts/branch-sync-update.sh --mode rebase`, permanecendo em no-op seguro com `ahead=0` e `behind=0`.
- A feature `F02-spec-engine-mvp` passou a ter `SPEC.md` propria, fixtures de SPEC valida/invalida e um validador minimo de `SPEC_VALIDATION` com parser de front matter YAML, checagem de campos obrigatorios e exigencia das secoes `Contexto` e `Objetivo`.
- A validacao local da `F02-spec-engine-mvp` foi concluida com testes verdes para o novo `SpecValidator`, mantendo o recorte da feature sem antecipar state machine, pipeline completa ou editor de SPEC.
- O `security-review` da `F02-spec-engine-mvp` foi aprovado com ressalvas baixas: manter `yaml.safe_load` e, na integracao futura, restringir o chamador a paths esperados de `SPEC.md` dentro do workspace da run.
- A PR `#19` da `F02-spec-engine-mvp` teve o gate `repo-checks` restaurado com correcao minima de formatacao, import order e compatibilidade de `mypy` no `SpecValidator`, sem ampliar o escopo da feature.
- O `security-review` mais recente da correcao da F02 aprovou o delta com ressalva baixa e localizada: o `# type: ignore[import-untyped]` em `yaml` e aceitavel neste recorte, mas pode ser removido depois com tipagem mais explicita ou `types-PyYAML`.
- A `F03-state-machine-mvp` passou a ter `SPEC.md` propria, state machine minima do AIgnt-Synapse-Flow com transicoes lineares validas, bloqueio de `PLAN` antes de `SPEC_VALIDATION` e estado terminal `FAILED`, com testes verdes e PR `#20` aberta.
- O `security-review` da `F03-state-machine-mvp` foi aprovado com ressalvas baixas: os estados ainda sao modelados como strings livres e `TERMINAL_STATES` ainda nao e usada explicitamente nas validacoes internas.
- A `F03-state-machine-mvp` ficou autocontida na worktree atual com materializacao de `features/F03-state-machine-mvp/SPEC.md`, mantendo alinhamento com o recorte aprovado da feature.
- A validacao local da `F03-state-machine-mvp` confirmou `5` testes unitarios verdes para a state machine minima, e o proximo passo logico permanece fechar `REPORT/COMMIT` antes de abrir a `F04`.
- A `F03-state-machine-mvp` foi encerrada: correcao de `B905` (`zip()` com `strict=False`), rebase sobre `main` atualizado, 10/10 checks CI verdes, PR `#20` mergeada por merge commit em `main`. Worktree e branch local removidos.
- O commit `chore(repo): add copilot instructions and codex MCP servers` incluiu `.github/copilot-instructions.md` (instrucoes de projeto com regra de idioma portugues) e `.codex/config.toml` com 4 MCP servers essenciais (GitHub, GitHub Actions, Docker, SQLite).

## Pendências abertas

- Fixtures de testes aspiracionais marcadas como 🔜 no TDD.md: `tests/fixtures/worker/` (ainda ausente).
- Property-based testing com `hypothesis` ainda não implementado (mencionado como evolução futura em TDD.md).
- Fechar a `chore-post-f47-baseline-handoff-sync` atualizando `PENDING_LOG.md`, `memory.md`, `docs/IDEAS.md`, `README.md` e `CHANGELOG.md` ao estado pos-`F47`.
- Rodar nova `technical-triage` depois da `chore-post-f47-baseline-handoff-sync` para escolher a proxima frente fora de `remote_multi_host_auth`.
- Manter `remote_multi_host_auth` explicitamente adiado ate existir demanda concreta, recorte proprio e validavel.

## Pontos de atenção futuros

- O bloqueio operacional de autenticacao do Codex (`401 Unauthorized`) ficou explicitamente classificado na F12; revalidar esse smoke apenas quando houver credencial valida e necessidade real de uso autenticado.
- A `F29` fechou apenas a fundacao local de auth/RBAC; nao assumir que `socket + RBAC` da `IDEA-001` foi totalmente absorvido sem uma nova SPEC especifica para operacao remota.

- Validar em momento futuro uma operacao real do MCP oficial do GitHub com credencial valida, pois a frente atual fechou apenas o startup path e a cobertura operacional do launcher.
- Fixture `noisy_mixed_output.txt` e `noisy_no_code_block.txt` armazenam sequências ANSI como literais `\u001b`. Todo helper que os lê para testar comportamento de ANSI precisa de `unicode_escape=True`. Considerar adicionar comentário nos próprios arquivos de fixture documentando isso.
- A ampliação de `TRANSPORT_NOISE_PREFIXES` para incluir prefixos como `[rpc]` deve ser decisão explícita documentada na SPEC da feature responsável — não uma adição silenciosa.
- Os testes de `test_review_rework.py` exercitam a state machine diretamente para estados CODE_GREEN/REVIEW/SECURITY que ainda não estão implementados no `PipelineEngine`. Quando o Supervisor/pipeline for implementado para esses estados, esses testes servem como documentação de comportamento esperado e devem ser migrados para testes de integração.
- O retry/reroute da F09 permanece restrito a uma unica execucao do AIgnt-Synapse-Flow; retomada persistida entre polls do worker e requeue duravel continuam fora de escopo.
- Em worktree fria, `pytest` e `uv run pytest` podem falhar na coleta ate que `uv sync --locked --extra dev` tenha sido executado.

- O fallback de `GITHUB_TOKEN` para `GITHUB_PERSONAL_ACCESS_TOKEN` continua aceitavel para o baseline atual, mas pode merecer opt-in explicito se gerar ambiguidade operacional em ambientes com tokens preexistentes.
- O helper `scripts/render-codex-config.sh` continua restrito ao launcher atual; se passar a ser reutilizado fora desse fluxo, vale endurecer os paths aceitos.
- `uv run --no-sync` continua dependendo de ambiente previamente sincronizado; em worktree fria ele pode cair no Python do host e falhar por dependências ausentes.
- O fluxo local com `.venv` pode exigir `PYTHONPATH=src` quando não se usa `uv run`; por isso ele continua apenas como fallback operacional e não como caminho padrão.
- O hardening do runtime valida identidade do processo por marcador + token em `/proc/<pid>/cmdline`; isso continua Linux-first.
- A validação do diretório configurável de estado permanece propositalmente básica no MVP e pode ser endurecida depois com âncora explícita no workspace.
- O runtime persistente continua propositalmente restrito a processo único local, sem scheduler, distribuição ou recuperação avançada.
- No uso diário do Codex em container, prefira `./scripts/dev-codex.sh` como entrypoint principal para evitar corrida operacional com `docker compose ... up` manual sobre o mesmo serviço.
- No uso diário de sincronização com `main`, prefira `./scripts/branch-sync-check.sh` e `./scripts/branch-sync-update.sh` em vez de comandos Git ad hoc; a atualização automática continua propositalmente conservadora e pode exigir resolução manual.
- `memory.md` deve permanecer memória durável e reaproveitável, sem virar transcrição de conversa.
- O `memory-curator` deve consolidar estado e handoff, enquanto `ERROR_LOG.md` e `PENDING_LOG.md` seguem como trilha operacional detalhada.
- Na integracao futura do `SpecValidator`, o chamador deve restringir a leitura de `SPEC.md` a paths esperados do workspace para evitar ampliacao desnecessaria da superficie de entrada.
- O `# type: ignore[import-untyped]` em `yaml` da F02 permanece como mitigacao minima de tipagem; reavaliar remocao quando houver frente dedicada de endurecimento ou tipagem de dependencias.
- Na evolucao da state machine apos a F03, considerar encapsular estados em `Enum` ou aplicar `TERMINAL_STATES` de forma efetiva para reduzir risco de drift semantico sem ampliar esta feature.

## TUI — Ideia de feature futura (análise de viabilidade concluída)

- **Rich enriquecido (F13-rich-cli-output)**: concluida localmente como primeira adocao de Rich em `src/`, restrita a `aignt runtime status` e sem abrir TUI completa.
- **Observabilidade CLI de runs (F14-runs-observability-cli)**: concluida localmente e fecha a lacuna minima de inspecao antes de qualquer TUI.
- **TUI watch (F14-tui-watch-command)**: `aignt tui` como subcomando opcional usando Textual. Pré-requisito atualizado: F13 + F14 + implementação de `observability/` (diretório ainda vazio). Hook ideal já existe: `PipelineObserver` em `pipeline.py`.
- **Constraint Typer×asyncio**: `asyncio.run(app.run_async())` dentro do comando Typer é a forma de coexistência; funcional mas exige cuidado com event loop.
- **TTY em container**: Rich degrada automaticamente sem TTY; Textual exige guarda `sys.stdout.isatty()`.
- **Não implementar antes**: apesar da F14 resolver a observabilidade minima via CLI, TUI real continua dependendo de recorte proprio de watch/streaming e da camada `observability/`.

## Estado do baseline atual

- Etapa 2 concluída em `main` com `F17-artifact-preview` e `F22-release-readiness` já mergeadas.
- A primeira onda de guardrails pós-release também está concluída em `main` com `F23 -> F27`.
- A fila ativa agora passa a ser definida pela próxima SPEC pós-`F27`, não mais pela abertura da primeira SPEC pós-`F22`.

## Guardrails candidatos fora da fila principal

- Os follow-ups curtos de mascaramento publico e normalizacao textual deixaram de ser candidatos: esses recortes foram absorvidos na `F23`.
- Rate limiting por adapter, audit trail adicional com `initiated_by` e hardening amplo de config tambem deixaram de ser backlog aberto isolado: esses recortes foram absorvidos em `F26` e `F27`.
- Os itens de guardrail ainda em aberto concentram-se em `G-09` e `G-11`.

## Itens que podem virar novas features ou ajustes futuros

- Endurecimento adicional do path de estado para restringir explicitamente a uma raiz confiável do workspace.
- Melhoria de portabilidade do runtime além de Linux, caso isso entre no escopo futuro.
- Documentação operacional curta para bootstrap local (`--sync-dev`) e para o lifecycle do runtime persistente.
- Limpeza operacional do repositório para remover debt de formatação fora do escopo desta feature.
- Integracao do `SpecValidator` ao fluxo seguinte da pipeline, incluindo bloqueio formal antes de `PLAN`.
- Evolucao da state machine para suportar estados adicionais como `RETRYING`, integracao com executor de steps e persistencia do estado fora do recorte minimo da F03.
