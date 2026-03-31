---
feature_id: F58
feature_name: Retry Policy Tests
status: draft
author: opencode
created: 2026-03-31
---

# F58 — Retry Policy Tests

## Objetivo

Criar suíte de testes dedicada para o módulo de supervisor/retry (`src/synapse_os/supervisor.py`), cobrindo decisões de retry, reroute, falhas terminais e retorno de REVIEW para CODE_GREEN. O módulo já existe mas não possui testes unitários dedicados — apenas testes indiretos em `test_supervisor.py` (4 testes existentes).

## Por que isso importa

O supervisor é o cérebro de recuperação de falhas do pipeline. Sem testes dedicados:

- Budget de retry pode ser consumido incorretamente
- Reroute pode não ser acionado quando deveria
- Falhas terminais podem ser tratadas como retryáveis

## Escopo

### Incluído

- Testes para `decide_after_failure` com estados retryáveis (PLAN, TEST_RED, CODE_GREEN)
- Testes para `decide_after_failure` com estados terminais (SPEC_VALIDATION, SECURITY)
- Testes para exhaustion de retry budget com reroute fallback
- Testes para `decide_after_review_rejection` retornando a CODE_GREEN
- Testes para ReviewRejectedError em estado REVIEW
- Testes para RetryableStepError em estados não-retryáveis

### Não incluído

- Testes de integração com pipeline real
- Testes de concorrência

## Critérios de Aceite

- [ ] AC1: `test_supervisor_requests_retry_after_recoverable_step_failure` — retry com budget disponível
- [ ] AC2: `test_supervisor_reroutes_after_repeated_step_failures` — reroute após budget esgotado
- [ ] AC3: `test_supervisor_marks_terminal_failure_after_spec_validation_error` — SPEC_VALIDATION é terminal
- [ ] AC4: `test_supervisor_marks_terminal_failure_after_security_error` — SECURITY é terminal
- [ ] AC5: `test_supervisor_returns_to_code_green_after_review_rejection` — REVIEW → CODE_GREEN
- [ ] AC6: `test_supervisor_terminal_failure_when_no_fallback_route` — fail sem fallback
- [ ] AC7: `test_supervisor_retry_budget_exhausted_at_max_retries` — retry no limite exato
- [ ] AC8: `test_supervisor_reroute_when_budget_exceeded_with_fallback` — reroute com fallback disponível
- [ ] AC9: `test_supervisor_ignores_retryable_error_in_non_retryable_state` — estado não-retryável → fail
- [ ] AC10: `test_supervisor_decision_contains_correct_reason` — reason field correto em cada cenário

## Design de Testes

### Fixtures

- `Supervisor` com max_retries=2
- Estados retryáveis: PLAN, TEST_RED, CODE_GREEN
- Estados terminais: SPEC_VALIDATION, SECURITY
- Exceções: RetryableStepError, ReviewRejectedError, RuntimeError genérico

## Dependências

- `src/synapse_os/supervisor.py` — módulo alvo
- `src/synapse_os/state_machine.py` — PipelineState
