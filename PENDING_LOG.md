# PENDING_LOG

## Decisões incorporadas recentemente

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

- Commit, push e PR da branch `feature/f09-supervisor-mvp` ainda pendentes.
- Revisar o delta final da F09 no fluxo Git (`REPORT` e `COMMIT`) antes de abrir a proxima feature.
- Definir a frente seguinte apos o fechamento da F09; o proximo passo natural continua sendo `F10` para `RUN_REPORT.md` e 1 adapter real.
- Revisão dos `NOTES.md` de cada feature (F01–F07) para verificar se referenciam conceitos obsoletos (estados `INIT`/`RETRYING`, `parser_confidence`, `REQUEST.md` como artefato).
- Verificar se SPECs F01–F05 usam `## 1. Contexto` (H2) em vez de `# Contexto` (H1) — o validator exige H1. Ainda não foi confirmado se esses SPECs passam no `validate_spec_file()`. Pode exigir atualização das SPECs ou confirmação de que a regra H1 se aplica apenas ao validator e não ao formato de seções do corpo da SPEC.
- Fixtures de testes aspiracionais marcadas como 🔜 no TDD.md: `tests/fixtures/worker/` (ainda ausente).
- Property-based testing com `hypothesis` ainda não implementado (mencionado como evolução futura em TDD.md).

## Pontos de atenção futuros

- Validar em momento futuro uma operacao real do MCP oficial do GitHub com credencial valida, pois a frente atual fechou apenas o startup path e a cobertura operacional do launcher.
- Fixture `noisy_mixed_output.txt` e `noisy_no_code_block.txt` armazenam sequências ANSI como literais `\u001b`. Todo helper que os lê para testar comportamento de ANSI precisa de `unicode_escape=True`. Considerar adicionar comentário nos próprios arquivos de fixture documentando isso.
- A ampliação de `TRANSPORT_NOISE_PREFIXES` para incluir prefixos como `[rpc]` deve ser decisão explícita documentada na SPEC da feature responsável — não uma adição silenciosa.
- Os testes de `test_review_rework.py` exercitam a state machine diretamente para estados CODE_GREEN/REVIEW/SECURITY que ainda não estão implementados no `PipelineEngine`. Quando o Supervisor/pipeline for implementado para esses estados, esses testes servem como documentação de comportamento esperado e devem ser migrados para testes de integração.
- O retry/reroute da F09 permanece restrito a uma unica execucao do AIgnt-Synapse-Flow; retomada persistida entre polls do worker e requeue duravel continuam fora de escopo.
- Em worktree fria, `pytest` e `uv run pytest` podem falhar na coleta ate que `uv sync --locked --extra dev` tenha sido executado.
- H1 vs H2 nas SPECs F01–F05: checar se `## 1. Contexto` causa falha de validação no `SpecValidator` após a regra H1 ter sido documentada.

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

## Itens que podem virar novas features ou ajustes futuros

- Endurecimento adicional do path de estado para restringir explicitamente a uma raiz confiável do workspace.
- Melhoria de portabilidade do runtime além de Linux, caso isso entre no escopo futuro.
- Documentação operacional curta para bootstrap local (`--sync-dev`) e para o lifecycle do runtime persistente.
- Limpeza operacional do repositório para remover debt de formatação fora do escopo desta feature.
- Integracao do `SpecValidator` ao fluxo seguinte da pipeline, incluindo bloqueio formal antes de `PLAN`.
- Evolucao da state machine para suportar estados adicionais como `RETRYING`, integracao com executor de steps e persistencia do estado fora do recorte minimo da F03.
