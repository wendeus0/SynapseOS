---
id: F28-adapter-circuit-breaker
type: feature
summary: Persistir um circuit breaker local para o adapter real atual, cobrindo G-09 com cooldown entre runs sem reabrir auth, SQLite ou CLI publica.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - src/aignt_os/adapters.py
  - src/aignt_os/config.py
  - src/aignt_os/runtime/state.py
outputs:
  - adapter_circuit_breaker_state
  - adapter_health_guard
  - feature_notes
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas o recorte de G-09"
  - "integrar o breaker persistido apenas ao CodexCLIAdapter nesta frente"
  - "nao alterar a CLI publica nem exigir novo subcomando"
  - "nao introduzir SQLite, Alembic, auth, RBAC ou coordenacao distribuida"
  - "preservar timeout, sanitizacao, max_concurrent_adapters e classificacao operacional ja existentes"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de boot, ciclo de vida em container ou integracao real"
acceptance_criteria:
  - "Existe um store local em arquivo JSON sob runtime_state_dir para persistir o estado do circuit breaker por adapter, com escrita atomica e permissoes restritas."
  - "AppSettings expõe `adapter_circuit_breaker_failure_threshold: int = 2`, `adapter_circuit_breaker_cooldown_seconds: float = 60.0` e o path derivado do arquivo de estado do breaker."
  - "Duas falhas operacionais consecutivas do Codex (`launcher_unavailable`, `container_unavailable`, `authentication_unavailable`) abrem o breaker e bloqueiam novas execucoes enquanto o cooldown estiver ativo, sem chamar subprocesso."
  - "Apos o cooldown, a proxima tentativa real do Codex e permitida; sucesso ou falha nao operacional (`timeout` ou `return_code_nonzero`) fecham o breaker e limpam o contador operacional."
  - "CodexExecutionAssessment passa a distinguir `circuit_open` como bloqueio operacional explicito."
  - "Existe cobertura unitaria e de integracao para persistencia do store, bloqueio sem spawn, reset apos cooldown e nao-regressao das classificacoes atuais do adapter."
non_goals:
  - "generalizar o breaker para adapters que ainda nao existem no produto"
  - "implementar half-open sofisticado, metricas distribuidas ou coordenacao cross-process forte"
  - "mudar a CLI publica, runs show/list, doctor ou runtime worker fora do wiring minimo necessario"
  - "revisitar auth, preview de artifacts, provenance ou outros guardrails fora de G-09"
security_notes:
  - "o arquivo de estado do breaker deve ficar restrito ao runtime_state_dir com escrita atomica e permissoes privadas"
  - "o breaker deve reagir apenas a bloqueios operacionais ja classificados, sem mascarar falhas funcionais do adapter"
  - "o bloqueio `circuit_open` deve ser explicito e auditavel para o operador"
dependencies:
  - F12-codex-adapter-operational-hardening
  - F26-run-provenance-integrity
  - F27-adapter-concurrency-guard
---

# Contexto

Depois da F27, o adapter layer ja possui classificacao operacional explicita do Codex e um guard de concorrencia local por processo, mas ainda nao existe memoria persistida de health/cooldown entre runs. Hoje o `CodexCLIAdapter` continua tentando spawns repetidos mesmo quando o ambiente ja deixou claro que esta bloqueado por launcher, container ou autenticacao.

No baseline atual, o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS e opera em modo local, CLI-first e single-host. O menor recorte util para `G-09` e adicionar apenas um circuit breaker persistido em arquivo local, sem abrir SQLite, auth ou coordenacao distribuida.

# Objetivo

Adicionar um circuit breaker local e persistido para o `CodexCLIAdapter`, com threshold fixo pequeno, cooldown simples e recuperacao automatica apos tentativa posterior, preservando o contrato atual do adapter e sem mudar a CLI publica.

# Escopo

## Incluido

- store persistido do circuit breaker em arquivo JSON no runtime state dir
- configuracao minima em `AppSettings` para threshold, cooldown e path derivado
- wiring do breaker no `CodexCLIAdapter`
- categoria `circuit_open` em `CodexExecutionAssessment`
- cobertura unitaria e de integracao para persistencia, bloqueio sem spawn, cooldown e reset
- `NOTES.md` e `CHECKLIST.md` da feature

## Fora de escopo

- novo banco, tabela ou migration dedicada
- suporte concreto a outros adapters alem do `codex`
- retries automáticos, scheduler ou coordinacao entre maquinas/processos
- mudancas em `runs show`, `doctor`, `RUN_REPORT.md` ou novos eventos persistidos

# Requisitos funcionais

1. O sistema deve persistir o estado do breaker por adapter em arquivo local sob `runtime_state_dir`.
2. O `CodexCLIAdapter` deve consultar o breaker antes de abrir subprocesso.
3. O breaker deve abrir apos duas falhas operacionais consecutivas do Codex.
4. Enquanto o cooldown estiver ativo, novas execucoes devem ser bloqueadas sem spawn.
5. Apos o cooldown, a proxima tentativa deve ser executada normalmente.
6. Sucesso ou falha nao operacional devem fechar o breaker e zerar o contador operacional.
7. O resultado bloqueado deve ser classificado explicitamente como `circuit_open`.

# Requisitos nao funcionais

- o recorte deve caber em 1 a 3 dias
- a persistencia deve reutilizar o padrao atual de arquivo local atomico
- a mudanca deve ser pequena, reversivel e sem ADR nova
- a feature nao deve exigir `DOCKER_PREFLIGHT`

# Casos de erro

- arquivo de breaker inexistente
- arquivo de breaker corrompido
- duas falhas operacionais consecutivas do Codex
- cooldown ainda nao expirado
- tentativa apos cooldown falhando novamente de forma operacional
- tentativa apos cooldown falhando de forma nao operacional

# Cenarios verificaveis

## Cenario 1: breaker abre e bloqueia sem spawn

- Dado duas falhas operacionais consecutivas do Codex
- Quando uma terceira execucao for solicitada antes de o cooldown expirar
- Entao o subprocesso nao e iniciado
- E o resultado e classificado como `circuit_open`

## Cenario 2: cooldown permite recuperacao

- Dado um breaker aberto
- Quando o cooldown expirar
- Entao a proxima tentativa real do Codex e permitida
- E um sucesso fecha o breaker

## Cenario 3: falha nao operacional nao mantem breaker aberto

- Dado um breaker que liberou uma tentativa apos cooldown
- Quando o Codex falhar com `timeout` ou `return_code_nonzero`
- Entao o estado operacional acumulado e limpo
- E o breaker volta a fechado

## Cenario 4: estado persiste entre instancias

- Dado um breaker aberto pelo `CodexCLIAdapter`
- Quando uma nova instancia do adapter for criada no mesmo workspace
- Entao ela enxerga o estado persistido
- E respeita o cooldown sem depender de memoria de processo

# Observacoes

Esta frente fecha apenas o recorte minimo de `G-09` para o adapter real atual. Auth (`G-11`), half-open sofisticado, telemetria mais rica e coordenacao distribuida continuam fora para manter o repositorio fiel ao modelo spec-first, feature-by-feature e uma frente por vez.
