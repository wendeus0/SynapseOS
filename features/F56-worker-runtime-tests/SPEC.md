---
feature_id: F56
feature_name: Worker Runtime Tests
status: draft
author: opencode
created: 2026-03-31
---

# F56 — Worker Runtime Tests

## Objetivo

Criar suíte de testes dedicada para o RuntimeWorker (`src/synapse_os/runtime/worker.py`), cobrindo polling, lock de execução, owner skip, e geração de run report. O worker é metade do modelo de runtime dual (CLI efêmero + worker residente) e atualmente não possui testes dedicados — apenas testes indiretos em `test_pipeline_persistence.py`.

## Por que isso importa

O worker é responsável por consumir runs pendentes, adquirir lock, executar pipelines e prevenir dupla execução. Sem testes dedicados, qualquer alteração no worker pode introduzir regressões silenciosas em:

- Processamento duplicado de runs (lock failure)
- Runs pendentes não processadas (polling bug)
- Owner mismatch causando starvation de runs
- Falhas silenciosas durante execução de pipeline

## Escopo

### Incluído

- Testes unitários para `RuntimeWorker.poll_once()`
- Testes unitários para `RuntimeWorker._next_pending_run()` com owner filtering
- Testes unitários para `RuntimeWorker._runtime_owner()`
- Testes unitários para `RuntimeWorker._record_owner_skip_if_needed()`
- Testes unitários para `RuntimeWorker.sleep_when_idle()`
- Testes de lock: worker não processa run já locked
- Testes de retry: worker continua polling após falha de lock
- Testes de owner skip: run com initiated_by incompatível é pulada com evento registrado
- Testes de owner skip dedup: evento duplicado não é registrado se já existe idêntico
- Teste de `build_runtime_worker()` factory function

### Não incluído

- Testes de integração com Docker real
- Testes de concorrência real (multi-thread/process)
- Testes do `PersistedPipelineRunner` (já cobertos em `test_pipeline_persistence.py`)
- Testes do `RunRepository` (já cobertos em `test_persistence.py`)

## Critérios de Aceite

- [x] AC1: `test_worker_picks_pending_run_and_transitions_to_running` — worker seleciona run pendente e executa via runner
- [x] AC2: `test_worker_does_not_acquire_lock_for_already_locked_run` — worker pula run com lock ativo e continua polling
- [x] AC3: `test_worker_requeues_step_after_retryable_failure` — worker não crasha quando runner lança exceção (falha já persistida pelo runner observer)
- [x] AC4: `test_worker_generates_run_report_after_pipeline_completion` — run report é gerado após pipeline completar (verificado via runner mock)
- [x] AC5: `test_worker_does_not_process_run_already_in_completed_state` — worker ignora runs já completadas
- [x] AC6: `test_worker_skips_run_with_incompatible_runtime_owner` — worker pula run com initiated_by incompatível com runtime owner
- [x] AC7: `test_worker_records_owner_skip_event` — evento RUNTIME_OWNER_SKIP_EVENT é registrado quando run é pulada por owner mismatch
- [x] AC8: `test_worker_does_not_duplicate_owner_skip_event` — evento idêntico não é registrado se já existe no histórico da run
- [x] AC9: `test_worker_returns_none_when_no_pending_runs` — poll_once retorna None quando não há runs pendentes
- [x] AC10: `test_worker_sleeps_when_idle` — sleep_when_idle dorme pelo poll_interval_seconds configurado
- [x] AC11: `test_build_runtime_worker_constructs_with_correct_poll_interval` — factory function cria worker com settings corretos
- [x] AC12: `test_runtime_owner_returns_none_when_provider_is_none` — \_runtime_owner retorna None sem provider

## Design de Testes

### Mocking Strategy

- Mock `RunRepository` com métodos individuais (find_next_pending_run, acquire_lock, list_unlocked_pending_runs, get_latest_event, record_event)
- Mock `PersistedPipelineRunner` (run_existing)
- Mock `RuntimeStateStore` (read)
- Usar `unittest.mock.MagicMock` para repositórios — não SQLite real
- Mock `time.sleep` para testes de polling sem delay real

### Estrutura de Arquivos

```
tests/unit/
  test_worker_runtime.py      — testes do RuntimeWorker
```

### Fixtures Necessárias

- `pending_run_record` — RunRecord com status pending
- `completed_run_record` — RunRecord com status complete
- `locked_run_record` — RunRecord que falha em acquire_lock
- `runtime_state_running` — RuntimeState com status running e started_by
- `runtime_state_stopped` — RuntimeState com status stopped

## Riscos e Mitigações

| Risco                                                                          | Mitigação                                                                       |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| Testes acoplados a implementação interna (\_next_pending_run, \_runtime_owner) | Aceitável — são métodos privados mas com comportamento observável via poll_once |
| time.sleep real em testes                                                      | Mock time.sleep com patch                                                       |
| Exceção do runner swallowada silenciosamente                                   | Verificar que exceção não propaga mas run_id é retornado                        |

## Dependências

- `src/synapse_os/runtime/worker.py` — módulo alvo
- `src/synapse_os/persistence.py` — RunRepository, RunRecord, ArtifactStore, PersistedPipelineRunner
- `src/synapse_os/runtime/state.py` — RuntimeState, RuntimeStateStore
- `src/synapse_os/state_machine.py` — PipelineState
- `src/synapse_os/config.py` — AppSettings

## Notas

- O worker já existe e funciona — esta feature é puramente de testes
- Padrão: tests unitários em `tests/unit/` conforme TDD.md section 10
- Não criar diretório `tests/worker/` — manter em unit enquanto volume for pequeno
