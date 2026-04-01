---
id: F65-runtime-coordinator-hardening
type: feature
summary: Hardened RuntimeCoordinator with graceful degradation, improved lifecycle state transitions, observability events, and cleanup handlers.
status: draft
created: 2026-03-31
owner: agent
inputs: []
outputs: []
acceptance_criteria:
    - RuntimeCoordinator enters degraded mode when circuit breaker is open, continues serving healthy adapters
    - Lifecycle state transitions emit 'runtime.lifecycle.transition' events
    - RuntimeCoordinator emits 'runtime.starting', 'runtime.started', 'runtime.stopping', 'runtime.stopped' events
    - Shutdown handler drains pending work with timeout before force-kill
    - Health check returns DEGRADED status when any circuit breaker is open
    - All new unit tests pass; existing RuntimeCoordinator tests continue to pass
non_goals: []
---

# Contexto

O `RuntimeCoordinator` em `runtime/service.py` é o componente central que gerencia o ciclo de vida do runtime. Ele não tem atualmente:

- Modo degradado quando circuit breakers estão abertos
- Eventos de lifecycle completos
- Tratamento graceful de shutdown
- Health check granular
- Integração de observabilidade com o sistema de eventos existente

# Objetivo

Introduzir um **RuntimeCoordinator reforçado** que:

1. **Graceful degradation** — quando um circuit breaker está aberto, o coordinator continua operando com adapters saudáveis em vez de falhar completamente.
2. **Lifecycle events** — emite eventos `runtime.lifecycle.transition`, `runtime.starting`, `runtime.started`, `runtime.stopping`, `runtime.stopped`.
3. **Shutdown handler** — ao receber sinal de término, drena trabalho pendente com timeout antes de force-kill.
4. **Health check granular** — `GET /health` retorna `{"status": "DEGRADED"}` quando circuit breakers estão abertos, `{"status": "HEALTHY"}` quando tudo OK.
5. **Cleanup handlers** — hooks de cleanup registráveis para recursos que precisam de liberação no shutdown.

O `RuntimeCoordinator` existente é enhancement in-place (não um replace).

# Escopo

## Dentro do Escopo

- `RuntimeCoordinator` com `degraded_adapters` set e lógica de graceful degradation
- `lifecycle_event(event_name)` método
- `shutdown(timeout_seconds)` método com drain graceful
- `register_cleanup_handler(callback)` e `run_cleanup_handlers()`
- `health_status()` método returning `Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]`
- `RuntimeLifecycleEvent` Pydantic model para eventos de lifecycle
- Unit tests em `tests/unit/test_runtime_coordinator_hardening.py`

## Fora do Escopo

- Modificação de `RuntimeService` (separado em F70)
- Integração com o servidor HTTP de control plane
- Persistência de health status

# Arquivos

- `src/synapse_os/runtime/service.py` — atualizar `RuntimeCoordinator` com hardening
- `tests/unit/test_runtime_coordinator_hardening.py` — unit tests
