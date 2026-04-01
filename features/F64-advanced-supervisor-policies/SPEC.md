---
id: F64-advanced-supervisor-policies
type: feature
summary: Policy-driven supervisor with per-step retry limits, exponential backoff, error-category-aware policies, and fallback routing.
status: draft
created: 2026-03-31
owner: agent
inputs: []
outputs: []
acceptance_criteria:
    - Per-step max_retries overrides are respected (TEST_RED retries 5 times, PLAN retries only 2)
    - Exponential backoff delay doubles each attempt: base=1s produces [1s, 2s, 4s, 8s]
    - Backoff cap at max_delay_seconds (default 60s)
    - SECURITY and SPEC_VALIDATION remain terminal (0 retries)
    - AdapterOperationalError with category launcher_unavailable short-circuits without retry
    - Fallback route is tried when primary route exhausts retries
    - All new unit tests pass; existing supervisor tests continue to pass
non_goals: []
---

# Contexto

O `Supervisor` atual em `supervisor.py` suporta apenas três ações: `retry`, `reroute` e `fail`. Retry tem um contador plano `max_retries` aplicado a todos os steps. Não existe configuração de retry por step, nem backoff exponencial, nem integração com circuit-breaker, nem política adaptativa que considere categorias de erro.

O supervisor do Synapse-Flow precisa evoluir de um contador plano para um sistema driven por políticas onde diferentes categorias de erro, steps e adapters podem ter políticas de retry/comportamento distintas.

# Decisão

Introduzir um **supervisor orientado a políticas** que:

1. **Limites de retry por step** — `PLAN`, `TEST_RED`, `CODE_GREEN` cada um recebe seu próprio `max_retries` ao invés de compartilhar um orçamento plano.
2. **Backoff exponencial** — entre retries, o delay dobra: 1s, 2s, 4s, etc. Cap em 60s.
3. **Políticas cientes de categoria de erro** — `RetryableStepError` recebe retries; `AdapterOperationalError` tem short-circuit em categorias "launcher_unavailable".
4. **Roteamento com fallback** — quando adapter primário está indisponível, rotear para próximo adapter disponível.
5. **Políticas específicas por step** — SECURITY e SPEC_VALIDATION permanecem terminais (sem retries).

O modelo existente `SupervisorDecision` permanece inalterado — a nova lógica produz os mesmos tipos de decisão.

# Escopo

## Dentro do Escopo

- `RetryPolicy` Pydantic model: `max_retries`, `base_delay_seconds`, `max_delay_seconds`
- `StepPolicy` Pydantic model: override por step do `RetryPolicy`
- `SupervisorPolicies` Pydantic model: holds default policy + per-step overrides
- `AdvancedSupervisor` class extending `Supervisor` com decisões orientadas por política
- `calculate_backoff(attempt, base_delay, max_delay)` helper
- Unit tests em `tests/unit/test_supervisor_policies.py`

## Fora do Escopo

- Integração com circuit breaker (tratado separadamente via `AdapterCircuitBreakerStore`)
- Carregamento dinâmico de políticas via config em runtime
- Compartilhamento de orçamento entre steps (cada step tem orçamento independente)

# Arquivos

- `src/synapse_os/supervisor.py` — adicionar policy models, `calculate_backoff`, atualizar `Supervisor.decide_after_failure`
- `tests/unit/test_supervisor_policies.py` — unit tests

# Critérios de Aceite

| #   | Criterion                                                                                                   |
| --- | ----------------------------------------------------------------------------------------------------------- |
| 1   | Per-step `max_retries` overrides are respected (e.g., TEST_RED can retry 5 times while PLAN retries only 2) |
| 2   | Exponential backoff delay doubles each attempt: base=1s → [1s, 2s, 4s, 8s]                                  |
| 3   | Backoff cap at `max_delay_seconds` (default 60s)                                                            |
| 4   | SECURITY and SPEC_VALIDATION remain terminal (0 retries)                                                    |
| 5   | `AdapterOperationalError` with category `launcher_unavailable` short-circuits without retry                 |
| 6   | Fallback route is tried when primary route exhausts retries                                                 |
| 7   | All new unit tests pass; existing supervisor tests continue to pass                                         |
