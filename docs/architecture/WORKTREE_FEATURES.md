# Worktree de Features — AIgnt OS

## Objetivo
Organizar o desenvolvimento do projeto em features pequenas, isoladas por branch/worktree, seguindo a esteira definida no SDD e a ordem recomendada no TDD.

## Princípios
- Trabalhar **uma feature por vez**.
- Cada feature deve ter sua própria `SPEC.md`.
- Nenhuma feature entra em código antes da SPEC e dos testes mínimos.
- O MVP de 10 dias deve priorizar **núcleo funcional**: SPEC, state machine, parser, adapter base, AIgnt-Synapse-Flow linear como engine própria de pipeline, persistência, worker leve e `RUN_REPORT.md`.
- Adapters reais ficam limitados a **1 adapter real prioritário** no prazo de 10 dias.

## Sequência recomendada de features do MVP inicial

### F01 — Project Bootstrap & Contracts
**Objetivo:** preparar base do repositório, pyproject, lint, typing, modelos Pydantic e estrutura de testes.
**Entrega:** projeto inicial executável, models base, CI local mínima.
**Branch/worktree:** `feature/f01-bootstrap-contracts`

### F02 — SPEC Engine MVP
**Objetivo:** validar o formato híbrido da SPEC (Markdown + YAML) e bloquear avanço sem SPEC válida.
**Entrega:** `SpecValidator`, parser do front matter, fixtures de SPEC válida/inválida.
**Branch/worktree:** `feature/f02-spec-engine-mvp`

### F03 — State Machine MVP
**Objetivo:** modelar estados e transições da pipeline principal.
**Entrega:** state machine com transições válidas/ inválidas e testes.
**Branch/worktree:** `feature/f03-state-machine-mvp`

### F04 — Parsing Engine MVP
**Objetivo:** limpar outputs ruidosos, extrair blocos úteis e validar artefatos básicos.
**Entrega:** cleaners, extractors, validators, testes com snapshots.
**Branch/worktree:** `feature/f04-parsing-engine-mvp`

### F05 — CLI Adapter Base Async
**Objetivo:** criar contrato único para execução de ferramentas via subprocess assíncrono.
**Entrega:** `BaseCLIAdapter`, `CLIExecutionResult`, timeout e sanitização.
**Branch/worktree:** `feature/f05-cli-adapter-base`

### F06 — AIgnt-Synapse-Flow Linear
**Objetivo:** executar a esteira linear com step executor e hand-offs mínimos.
**Entrega:** `PipelineStep`, `StepExecutor`, `PipelineEngine`, fluxo até `PLAN` ou fluxo completo em fake mode.
**Branch/worktree:** `feature/f06-pipeline-engine-linear`

### F07 — Persistência Operacional + Artifact Store
**Objetivo:** salvar runs, steps, eventos, outputs brutos/limpos e artefatos da run.
**Entrega:** repositório SQLite, lock inicial, artifact store em filesystem.
**Branch/worktree:** `feature/f07-persistence-artifacts`

### F08 — Worker Leve + Runtime Dual
**Objetivo:** adicionar execução assíncrona para runs longas.
**Entrega:** polling de runs pendentes, locking, retomada básica, decisão sync/async por regra.
**Branch/worktree:** `feature/f08-worker-runtime-dual`

### F09 — Supervisor MVP + Retry/Reroute
**Objetivo:** decidir retry, reroute e falha terminal em cenários simples.
**Entrega:** `SupervisorDecision`, regras determinísticas, integração com pipeline.
**Branch/worktree:** `feature/f09-supervisor-mvp`

### F10 — RUN_REPORT + 1 Adapter Real
**Objetivo:** fechar o MVP com auditoria local e uma integração real mínima.
**Entrega:** `RUN_REPORT.md`, 1 adapter real (ex.: Codex CLI ou Gemini CLI), happy path de ponta a ponta.
**Branch/worktree:** `feature/f10-run-report-one-real-adapter`

## Follow-ups pós-MVP já concluídos

### F11 — Repo Automation
**Objetivo:** endurecer fluxo operacional do repositório, Docker e CI.
**Entrega:** scripts operacionais, `DOCKER_PREFLIGHT`, checks locais e governança contra drift.
**Branch/worktree:** `feature/f11-repo-automation`

### F12 — Codex Adapter Operational Hardening
**Objetivo:** endurecer o adapter real do Codex no fluxo container-first.
**Entrega:** classificação operacional de falhas e validação prática do caminho do launcher.
**Branch/worktree:** `feature/f12-codex-adapter-operational-hardening`

### F13 — Rich CLI Output
**Objetivo:** melhorar a UX inicial da CLI sem abrir TUI.
**Entrega:** saída enriquecida com Rich para `aignt runtime status`.
**Branch/worktree:** `feature/f13-rich-cli-output`

### F14 — Runs Observability CLI
**Objetivo:** expor inspeção pública de runs persistidas.
**Entrega:** `aignt runs list` e `aignt runs show <run_id>`.
**Branch/worktree:** `feature/f14-runs-observability-cli`

### F15 — Public Run Submission
**Objetivo:** expor submissao publica de runs pela CLI a partir de uma SPEC validada.
**Entrega:** `aignt runs submit <spec_path>` com `--mode auto|sync|async` e `--stop-at`.
**Branch/worktree:** `feature/f15-public-run-submission`

## Próxima etapa pós-F14

A fila ativa do projeto deixou de ser o cronograma histórico do MVP inicial. A nova etapa segue o **cenário misto** definido na triagem e está detalhada em `docs/architecture/PHASE_2_ROADMAP.md`.

### Sequência oficial remanescente da etapa 2

1. `F16-run-detail-expansion`
2. `F21-cli-error-model-and-exit-codes`
3. `F18-canonical-happy-path`
4. `F19-environment-doctor`
5. `F20-public-onboarding`
6. `F17-artifact-preview`
7. `F22-release-readiness`

### Padrão mínimo de descrição por feature

Cada frente da etapa 2 deve ser documentada pelo menos com:
- objetivo
- valor para a fase
- superfície pública afetada
- dependências
- fora de escopo
- critério de pronto
- risco principal

### Guardrails candidatos antes da etapa 2

Propostas de hardening sobre input, secrets, rate limiting e audit trail foram avaliadas antes da abertura da etapa 2.

Diretriz atual:
- nao abrir essas propostas como features autonomas fora da fila principal da etapa 2;
- nao reciclar IDs ja usados (`F14`) nem o ID reservado da `F15`;
- permitir apenas um follow-up curto de mascaramento de secrets em saidas `_clean` e artifacts publicos se surgir risco real antes da `F21`;
- absorver o restante dentro de `F21` ou de follow-up proprio curto, se houver necessidade concreta.

## Features que ficam fora do MVP de 10 dias
- DAG real com fan-out/fan-in
- múltiplos adapters reais
- memória vetorial
- roteamento automático pela memória semântica
- múltiplos workspaces por run
- paralelismo pesado

## Estrutura sugerida para specs por feature
```text
features/
  F01-bootstrap-contracts/
    SPEC.md
    NOTES.md
  F02-spec-engine-mvp/
    SPEC.md
    NOTES.md
  F03-state-machine-mvp/
    SPEC.md
    NOTES.md
  F04-parsing-engine-mvp/
    SPEC.md
    NOTES.md
  F05-cli-adapter-base/
    SPEC.md
    NOTES.md
  F06-pipeline-engine-linear/
    SPEC.md
    NOTES.md
  F07-persistence-artifacts/
    SPEC.md
    NOTES.md
  F08-worker-runtime-dual/
    SPEC.md
    NOTES.md
  F09-supervisor-mvp/
    SPEC.md
    NOTES.md
  F10-run-report-one-real-adapter/
    SPEC.md
    NOTES.md
```

## Critério de conclusão por feature
Uma feature só fecha quando tiver:
1. `SPEC.md` aprovada
2. testes mínimos passando
3. código integrado
4. atualização do relatório/notas da feature
5. sem pendência crítica escondida
