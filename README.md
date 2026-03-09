# AIgnt OS

> Meta-orquestrador de agentes de IA via CLI — produz software com rastreabilidade, resiliência e baixo custo operacional.

---

## O que é o AIgnt OS?

O AIgnt OS é um **orquestrador de ferramentas externas de IA via CLI**. Em vez de chamar APIs diretamente, ele executa ferramentas como Gemini CLI, Codex CLI, Claude CLI e outras por subprocess, coordenando hand-offs entre etapas de uma esteira de desenvolvimento autônomo.

O sistema recebe uma tarefa, produz uma especificação estruturada, planeja a execução, aciona agentes externos, limpa e valida suas saídas, reage a falhas e entrega um relatório auditável por run.

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

## Objetivo do MVP

Entregar, em 10 dias de trabalho focado, o **núcleo funcional mínimo** do sistema:

```
CLI funcional → SPEC válida → State Machine → Parser → Adapter base async
     → Pipeline linear → Persistência → Worker leve → Supervisor → RUN_REPORT.md
                                                             → 1 adapter real
```

### Esteira principal do MVP

```
REQUEST → SPEC_DISCOVERY → SPEC_NORMALIZATION → SPEC_VALIDATION
       → PLAN → TEST_RED → CODE_GREEN → REVIEW → SECURITY → DOCUMENT → COMPLETE
```

### Entregas obrigatórias

- `SPEC_VALIDATION` bloqueando avanço para `PLAN` quando a spec for inválida
- State machine com transições auditáveis
- Parsing robusto de outputs ruidosos de CLIs
- Adapter base assíncrono com timeout, sanitização e contrato único
- Engine própria de pipeline linear (sem dependência de orquestrador externo)
- Persistência operacional (SQLite + artifacts em disco)
- Worker leve com polling, lock e retomada de runs
- Supervisor com retry determinístico, reroute simples e falha terminal
- Geração de `RUN_REPORT.md` por execução
- 1 adapter real integrado e testado ponta a ponta

### Artefatos gerados por run

```
artifacts/<run_id>/
  REQUEST.md
  SPEC.md
  PLAN.md
  TESTS_RED.md
  <código gerado>
  REVIEW.md
  SECURITY.md
  DOCUMENT.md
  RUN_REPORT.md
```

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
├── architecture/          # Documentação técnica de referência
│   ├── SDD.md             # Software Design Document — arquitetura completa
│   ├── TDD.md             # Estratégia de testes e ordem de implementação
│   ├── IMPLEMENTATION_STACK.md   # Stack e justificativas
│   ├── CRONOGRAMA_10_DIAS.md     # Roadmap do MVP feature a feature
│   ├── WORKTREE_FEATURES.md      # Sequência e escopo de cada feature
│   ├── SPEC_FORMAT.md            # Formato oficial da SPEC híbrida
│   └── SPEC_TEMPLATE_v2.md       # Template de SPEC para novas features
│
├── docs/
│   └── adr/               # Architecture Decision Records
│       ├── 001-cli-orchestration.md
│       ├── 002-python-orchestrator.md
│       ├── 003-state-machine-pipeline-engine.md
│       ├── 004-cli-adapter-layer.md
│       ├── 005-semantic-memory.md
│       ├── 006-regex-based-parsing.md
│       ├── 007-local-llms-offline-reasoning.md
│       ├── 008-spec-driven-development.md
│       └── 009-runtime-dual-cli-worker.md
│
├── features/              # SPECs e notas por feature do MVP
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

1. **Entender o sistema** → leia `architecture/SDD.md`
2. **Entender as decisões** → navegue pelos ADRs em `docs/adr/`
3. **Contribuir com uma feature** → consulte `architecture/WORKTREE_FEATURES.md` e use `architecture/SPEC_TEMPLATE_v2.md` para criar sua `SPEC.md` antes de qualquer código
4. **Entender a estratégia de testes** → leia `architecture/TDD.md`
5. **Ver o roadmap do MVP** → `architecture/CRONOGRAMA_10_DIAS.md`

---

## Desenvolvimento por feature

O desenvolvimento segue o ciclo **Spec-first → Red → Green → Refactor**, com uma feature por worktree:

```
feature/f01-bootstrap-contracts
feature/f02-spec-engine-mvp
feature/f03-state-machine-mvp
feature/f04-parsing-engine-mvp
feature/f05-cli-adapter-base
feature/f06-pipeline-engine-linear
feature/f07-persistence-artifacts
feature/f08-worker-runtime-dual
feature/f09-supervisor-mvp
feature/f10-run-report-one-real-adapter
```

Nenhuma feature avança para código sem `SPEC.md` aprovada e testes mínimos escritos.
