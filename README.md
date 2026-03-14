# AIgnt OS

> Meta-orquestrador de agentes de IA via CLI — produz software com rastreabilidade, resiliência e baixo custo operacional.

---

## O que é o AIgnt OS?

O AIgnt OS é um **orquestrador de ferramentas externas de IA via CLI**. Em vez de chamar APIs diretamente, ele executa ferramentas como Gemini CLI, Codex CLI, Claude CLI e outras por subprocess, coordenando hand-offs entre etapas de uma esteira de desenvolvimento autônomo.

O sistema recebe uma tarefa, produz uma especificação estruturada, planeja a execução, aciona agentes externos, limpa e valida suas saídas, reage a falhas e entrega um relatório auditável por run.

O runtime interno é coordenado pelo **AIgnt-Synapse-Flow**, a **engine própria de pipeline** do AIgnt OS.

### Princípios fundamentais

| Princípio | Descrição |
|---|---|
| **CLI-first** | Integrações externas passam por adapters padronizados via subprocess |
| **Spec-first** | A demanda bruta vira contrato operacional antes de qualquer execução |
| **State-driven** | O fluxo é auditável por máquina de estados, evolutivo para DAG |
| **Structured handoff** | Nenhuma etapa consome saída bruta sem parsing e validação |
| **Failure-aware** | Falhas são esperadas, classificadas e tratadas |
| **Observability by default** | Logs estruturados e `RUN_REPORT.md` por execução são parte da arquitetura |

---

## Baseline Atual do Repositório

O AIgnt OS ja ultrapassou o recorte inicial de MVP e hoje expõe um baseline tecnico coerente para submissao, observabilidade e operacao local de runs. O AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS e o repositorio atual ja incorpora:

- etapa 2 consolidada com `doctor`, `runs submit`, `runs show`, artifact preview e onboarding publico local
- guardrails pos-release absorvidos (`F23 -> F27`) para sanitizacao, boundary de workspace/artifacts, AST guard, provenance e concorrencia local
- auth local e RBAC absorvidos (`F29`, `F30`, `F44`, `F47`) com `auth_provider=file` e roles fixas `viewer`, `operator`, `admin`
- ownership local do runtime absorvida (`F32`, `F34`, `F35`, `F36`) para o recorte residente/local de auth
- dashboard TUI local e observabilidade adicional absorvidos (`F40`, `F41`, `F42`, `F45`) com logs, artifacts, filtros e cancelamento local/gracioso
- robustez de runtime absorvida (`F43`) com timeout global por step e retry simples para falhas transientes

### Fluxo oficial do repositório

```
SPEC → TEST_RED → CODE_GREEN → REFACTOR → QUALITY_GATE → SECURITY_REVIEW → REPORT → COMMIT
```

Dentro do macroestágio `SPEC`, o AIgnt-Synapse-Flow pode decompor a execução em `SPEC_DISCOVERY`, `SPEC_NORMALIZATION` e `SPEC_VALIDATION`.

O `DOCKER_PREFLIGHT` do projeto continua sendo gate operacional condicional. Por padrão, ele é leve: valida apenas `compose config`, sem build nem `up`. O build explícito fica para workflows e comandos de imagem, e o runtime completo fica para workflow dedicado de integração/runtime ou para execução explícita quando a feature tocar boot, ciclo de vida, persistência ou integração. Os hooks locais continuam leves e não substituem o `DOCKER_PREFLIGHT` operacional real.

### Superfície pública atual da CLI

- `aignt doctor`
- `aignt runs submit <spec_path> --mode auto|sync|async --stop-at <STEP>`
- `aignt runs list`
- `aignt runs show <run_id>`
- `aignt runs show <run_id> --preview report`
- `aignt runs watch <run_id>`
- `aignt runs cancel <run_id>`
- `aignt auth init|issue|disable`
- `aignt runtime start|status|run|ready|stop`

### Boundaries atuais do baseline

- o baseline publico continua local e CLI-first; nao existe web UI nem operacao distribuida
- watch, filtros e cancelamento continuam locais; nao ha scheduler, fila remota nem cancelamento multi-host
- auth e RBAC continuam locais com provider `file`; auth remota e rotacao distribuida seguem fora de escopo
- o runtime residente continua leve e local; sync e async coexistem no mesmo baseline

---

## Stack

### Core

| Tecnologia | Uso |
|---|---|
| **Python 3.12+** | Linguagem principal |
| **Typer** | Interface CLI moderna com type hints |
| **Rich** | UX no terminal (progress, tabelas, logs) |
| **asyncio + asyncio.create_subprocess_exec()** | Execução assíncrona de CLIs externas |
| **python-statemachine** | Modelagem explícita de estados e transições |

### Contratos e validação

| Tecnologia | Uso |
|---|---|
| **Pydantic v2** | Contratos internos e modelos de domínio |
| **pydantic-settings** | Configuração via env/arquivo |
| **jsonschema** | Validação do schema da SPEC |
| **re + ast** | Parsing de outputs e validação de código Python |

### Persistência

| Tecnologia | Uso |
|---|---|
| **SQLAlchemy 2 + SQLite** | Metadados operacionais de runs/steps/eventos |
| **Alembic** | Migrações do banco |
| **Filesystem** | Artefatos brutos, limpos e relatórios |

### Observabilidade

| Tecnologia | Uso |
|---|---|
| **structlog** | Logs estruturados por run e step |

### Qualidade

| Tecnologia | Uso |
|---|---|
| **pytest + pytest-asyncio + pytest-mock + Hypothesis** | Testes unitários, integração, pipeline e worker |
| **uv** | Gerenciamento de dependências e ambiente |
| **Ruff** | Linting e formatação |
| **mypy** | Verificação de tipos estáticos |

---

## Como navegar no repositório

```
aignt-os/
├── docs/
│   ├── architecture/      # Documentação técnica de referência
│   │   ├── SDD.md             # Software Design Document — arquitetura completa
│   │   ├── TDD.md             # Estratégia de testes e ordem de implementação
│   │   ├── IMPLEMENTATION_STACK.md   # Stack e justificativas
│   │   ├── CRONOGRAMA_10_DIAS.md     # Roadmap do MVP feature a feature
│   │   ├── WORKTREE_FEATURES.md      # Sequência e escopo de cada feature
│   │   ├── SPEC_FORMAT.md            # Formato oficial da SPEC híbrida
│   │   └── SPEC_TEMPLATE_v2.md       # Template de SPEC para novas features
│   │
│   └── adr/               # Architecture Decision Records
│       ├── 001-cli-orchestration.md
│       ├── 002-python-orchestrator.md
│       ├── 003-state-machine-pipeline-engine.md
│       ├── 004-cli-adapter-layer.md
│       ├── 005-semantic-memory.md
│       ├── 006-regex-based-parsing.md
│       ├── 007-local-llms-offline-reasoning.md
│       ├── 008-spec-driven-development.md
│       ├── 009-runtime-dual-cli-worker.md
│       ├── 010-adopt-aignt-synapse-flow-name.md
│       ├── 011-lightweight-docker-preflight-default.md
│       └── 012-mandatory-integration-tests.md
│
│   └── operations/        # Manuais operacionais e lifecycle
│       └── LIFECYCLE.md      # Guia de bootstrap, runtime e pipeline
│
├── features/              # SPECs e notas por feature
│   └── init_feature_worktrees.sh  # Script para criar worktrees das features
│
├── src/
│   └── aignt_os/          # Código-fonte principal
│
└── tests/                 # Suíte de testes
    ├── unit/              # Testes unitários (parser, spec, state machine…)
    ├── integration/       # Testes de integração (adapter+parser, CLI+pipeline…)
    ├── pipeline/          # Testes de happy path e recovery ponta a ponta
    └── fixtures/          # Outputs de CLIs, SPECs de exemplo, relatórios esperados
```

### Por onde começar

1. **Entender o sistema** → leia `docs/architecture/SDD.md`
2. **Entender as decisões** → navegue pelos ADRs em `docs/adr/`
3. **Contribuir com uma feature** → consulte `docs/architecture/WORKTREE_FEATURES.md` e use `docs/architecture/SPEC_TEMPLATE_v2.md` para criar sua `SPEC.md` antes de qualquer código
4. **Entender a estratégia de testes** → leia `docs/architecture/TDD.md`
5. **Ver o roadmap do MVP inicial** → `docs/architecture/CRONOGRAMA_10_DIAS.md`
6. **Ver o fechamento da etapa 2 e a transição pós-release** → `docs/architecture/PHASE_2_ROADMAP.md`
7. **Operar o sistema** → consulte `docs/operations/LIFECYCLE.md`

## Estado Atual do Projeto

O estado atual do repositório já vai além do fechamento da etapa 2. O quadro vigente combina:

- release técnica pública consolidada para o fluxo local `sync-first`
- hardening operacional e de artefatos pós-release
- auth local com RBAC e ownership local do runtime
- dashboard TUI local com visualização de logs, explorer de artifacts, filtros e cancelamento local
- manual operacional dedicado em `docs/operations/LIFECYCLE.md`

Para detalhes operacionais de bootstrap, lifecycle e pipeline, use `docs/operations/LIFECYCLE.md`. Para histórico formal de release, consulte `CHANGELOG.md` e `docs/release/`.

---

## Primeira Run Publica

O caminho oficial atual da primeira run continua local e `sync-first`. Use esta sequencia curta para validar o ambiente minimo, submeter uma SPEC e inspecionar o resultado sem depender de runtime residente.

### Quickstart oficial

1. Diagnostique o ambiente local com `aignt doctor`.
2. Se o doctor fechar sem falha bloqueante, envie a SPEC com `aignt runs submit <spec_path> --mode sync --stop-at SPEC_VALIDATION`.
3. Capture o `run_id` retornado pelo submit.
4. Inspecione o resultado com `aignt runs show <run_id>`.

### Boundary operacional

- `aignt doctor` e diagnostico local e advisory: ele verifica `runtime_state`, `runs_db` e `artifacts_dir` no ambiente atual.
- O doctor nao substitui `repo-preflight` para cenarios com Docker, container, build de imagem, boot de runtime persistente, persistencia operacional ou integracao real.
- Se a sua primeira execucao depender desses cenarios, saia do quickstart e rode o preflight operacional do projeto via `repo-preflight` (`./scripts/docker-preflight.sh`).
- `runtime_state=warn` nao bloqueia o caminho minimo atual, porque a demonstracao oficial continua local e `sync-first`; o status `warn` e advisory, nao falha bloqueante.

## Artifact Preview

O preview de artifacts e uma capacidade adicional da CLI publica, nao um requisito da primeira run minima. O quickstart continua local e `sync-first` ate `SPEC_VALIDATION`; o preview so aparece quando a run ja possui artifacts persistidos compativeis, como `RUN_REPORT.md` ou `clean_output` por step.

Exemplos suportados:

- `aignt runs show <run_id> --preview report`
- `aignt runs show <run_id> --preview PLAN.clean`

Limites do recorte atual:

- o preview continua textual e truncado no inicio do arquivo;
- `raw_output` continua fora de escopo;
- nao ha leitura arbitraria de path informado pelo usuario;
- se o artifact ainda nao existir, a CLI retorna `Not found:` conforme o contrato da F21.

## TUI Watch e Cancelamento Local

O dashboard TUI atual do AIgnt OS continua local e terminal-first. Ele observa uma run especifica ja persistida e renderiza o estado atual do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, sem abrir web UI nem operacao distribuida.

Superficie publica atual:

- `aignt runs watch <run_id>` abre o dashboard TUI local da run
- `aignt runs cancel <run_id>` solicita cancelamento local e gracioso da run

Atalhos reais do dashboard atual:

- `Enter` abre a aba de logs do step selecionado
- `a` abre o explorer de artifacts
- `f` filtra apenas steps `failed`
- `r` filtra steps `running` e `pending`
- `x` restaura a visualizacao de todos os steps
- `k` solicita cancelamento da run observada

Boundary do recorte atual:

- o watch/dashboard continua local; nao ha painel remoto, web UI nem streaming distribuido
- o cancelamento atual e apenas local e gracioso; nao existe `kill -9` nem interrupcao forcada de subprocessos externos
- nao ha scheduler, fila remota de cancelamento nem coordenacao multi-host
- os filtros atuais sao apenas visuais e nao persistem entre sessoes

## Auth Registry Local

A `F29` introduziu auth opt-in para os comandos mutaveis da CLI, a `F30` adicionou o provisionamento local desse registry sem editar JSON manualmente, a `F44` desacoplou o provider atual em torno de `auth_provider=file` e a `F47` consolidou RBAC local com roles fixas (`viewer`, `operator`, `admin`). O AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS; esta capacidade permanece estritamente local e nao abre socket, auth remota ou RBAC distribuido.

Fluxo minimo de provisionamento:

1. Inicialize o registry com `aignt auth init --principal-id local-admin --role admin`.
2. Emita um token adicional com `aignt auth issue --principal-id local-viewer --role viewer`.
3. Emita um token operacional com `aignt auth issue --principal-id local-operator --role operator`.
4. Se precisar revogar um token emitido, use `aignt auth disable --token-id <token_id>`.

Boundary de roles no recorte atual:

- `viewer` consegue consultar `runs list`, `runs show`, `runs watch`, `runs follow`, `doctor` e `version`, mas nao submete run nem gerencia runtime;
- `operator` herda leitura e pode operar `runs submit`, `runtime start|run|stop` e demais mutacoes operacionais de run;
- `admin` mantem acesso total, incluindo `auth init|issue|disable`;
- o provider atual continua sendo `file`; providers externos e auth remota continuam fora de escopo.

Boundary do recorte atual:

- o token bruto aparece apenas no stdout nominal de `init` e `issue`;
- o arquivo persistido guarda apenas `token_sha256`, `token_id`, `principal_id` e `disabled`;
- `runs submit` e `runtime start|run|stop` continuam exigindo token somente quando `auth_enabled=true`;
- comandos de leitura publica continuam sem token;
- roles novas continuam fixas no codigo; nao ha papeis arbitrarios definidos pelo usuario;
- operacao remota e rotacao distribuida continuam fora de escopo.

### Troubleshooting essencial

| Sinal | Leitura | Proximo passo |
|---|---|---|
| `runtime_state = warn` | O runtime persistente esta parado, mas o fluxo minimo atual ainda pode seguir. | Continue no quickstart `sync-first`; so escale para preflight/runtime se precisar de modo operacional mais pesado. |
| `runtime_state = fail` | O estado persistido do runtime esta inconsistente. | Corrija o estado local antes de prosseguir; se a execucao depender de runtime persistente ou container, use `repo-preflight`. |
| `runs_db = fail` | O caminho de persistencia SQLite nao pode ser preparado pelo processo atual. | Ajuste permissao ou configuracao do path antes de rodar `aignt runs submit`. |
| `artifacts_dir = fail` | O diretório de artifacts nao pode ser preparado pelo processo atual. | Ajuste permissao ou configuracao do path antes de inspecionar outputs persistidos. |
| `SPEC invalida` no submit | A SPEC nao passou em `SPEC_VALIDATION`. | Corrija o front matter YAML e as secoes `# Contexto` e `# Objetivo` antes de reenviar. |

## Operação e Desenvolvimento

O desenvolvimento continua feature-by-feature, com `SPEC.md` validada antes de código e uma feature por worktree.

### Checks locais vs. DOCKER_PREFLIGHT

- Hook local leve: `.githooks/pre-commit` roda `./scripts/commit-check.sh --hook-mode` para checks rápidos de repositório sem executar o preflight Docker real.
- Caminho operacional padrão para checks/testes locais: execute `./scripts/commit-check.sh --sync-dev` em uma branch de trabalho para sincronizar dependências dev no ambiente gerenciado por `uv` e rodar format, lint, typecheck e testes sem depender de `.venv` legada do host.
- Reexecução rápida depois do bootstrap: use `./scripts/commit-check.sh --no-sync` para repetir o fluxo operacional sem nova sincronização; `uv run --no-sync ...` continua útil para comandos pontuais, mas não é o ponto de entrada recomendado para preparar um ambiente local do zero.
- Virtualenv explícita com `PYTHONPATH=src` deve ficar restrita a fallback de diagnóstico ou recuperação de ambiente quando o fluxo padrão com `uv` estiver indisponível ou já classificado como problema externo ao repositório.
- Preflight Docker operacional real: execute `./scripts/docker-preflight.sh` antes de iniciar a execução prática da feature ou da IA quando a tarefa depender de Docker.
- Build explícito de imagem: execute `./scripts/docker-preflight.sh --build` quando o objetivo for validar a imagem Docker.
- Runtime completo: execute `./scripts/docker-preflight.sh --full-runtime` apenas quando a mudança tocar boot, ciclo de vida, persistência ou integração.

### Ambiente isolado do Codex

- O runtime da aplicação continua no serviço `aignt-os` definido em `compose.yaml`.
- O Codex roda isolado no serviço `codex-dev` definido em `compose.dev.yaml`, com apenas o repositório montado em `/workspace`.
- Para subir o ambiente e abrir o Codex dentro do container de desenvolvimento, use `./scripts/dev-codex.sh`.
- Para subir também o runtime existente junto com o ambiente de desenvolvimento, use `./scripts/dev-codex.sh --with-runtime`.
- O launcher aplica o profile `container_aggressive` de `.codex/config.toml` apenas dentro desse ambiente isolado.
- Para habilitar o MCP oficial do GitHub dentro do `codex-dev`, exporte `GITHUB_PERSONAL_ACCESS_TOKEN` antes de rodar o launcher. Se apenas `GITHUB_TOKEN` estiver definido, o launcher o reutiliza como fallback.
- O toolset `actions` do MCP oficial do GitHub cobre o caso de GitHub Actions; não há servidor `github-actions` separado no baseline atual.
- O MCP de SQLite fica desabilitado por padrão até existir um banco real a ser exposto no workspace.
- O MCP de Docker também fica fora do baseline do `codex-dev`, porque esse ambiente isolado não monta `docker.sock`.

### Referência operacional

- `docs/operations/LIFECYCLE.md` centraliza bootstrap, lifecycle do runtime residente e pipeline management.
- `CHANGELOG.md` e `docs/release/` guardam o histórico formal de release; o README resume apenas o quadro atual.
