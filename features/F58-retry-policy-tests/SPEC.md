---
id: F58-retry-policy-tests
type: feature
summary: Criar suíte de testes dedicada para o módulo de supervisor/retry cobrindo decisões de retry, reroute, falhas terminais e retorno de REVIEW para CODE_GREEN.
inputs:
    - Supervisor com max_retries configurável
    - RetryableStepError para falhas recuperáveis
    - ReviewRejectedError para rejeição de review
outputs:
    - SupervisorDecision com action, next_state, route e reason
    - Testes unitários cobrindo todos os caminhos de decisão
acceptance_criteria:
    - Dado Supervisor(max_retries=2) e RetryableStepError em estado retryável com attempt <= max_retries, quando decide_after_failure é chamado, então action=retry com reason=retryable_failure_with_budget
    - Dado Supervisor(max_retries=2) e RetryableStepError com attempt > max_retries e fallback_route disponível, quando decide_after_failure é chamado, então action=reroute com route=fallback
    - Dado estado SPEC_VALIDATION com qualquer erro, quando decide_after_failure é chamado, então action=fail com reason=spec_validation_is_terminal
    - Dado estado SECURITY com qualquer erro, quando decide_after_failure é chamado, então action=fail com reason=security_is_terminal
    - Dado ReviewRejectedError em estado REVIEW, quando decide_after_review_rejection é chamado, então action=return_to_code_green com next_state=CODE_GREEN
    - Dado RetryableStepError em estado não-retryável, quando decide_after_failure é chamado, então action=fail com reason=terminal_failure
non_goals:
    - Testes de integração com pipeline real
    - Testes de concorrência
---

# F58 — Retry Policy Tests

# Contexto

O módulo `src/synapse_os/supervisor.py` implementa o cérebro de recuperação de falhas do pipeline, decidindo entre retry, reroute ou falha terminal. Atualmente possui 4 testes indiretos em `test_supervisor.py`. Esta feature adiciona 6 testes dedicados cobrindo todos os caminhos de decisão.

# Objetivo

Criar suíte de testes dedicada para o supervisor cobrindo decisões de retry, reroute, falhas terminais e retorno de REVIEW para CODE_GREEN.

# Critérios de Aceite

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

# Design de Testes

### Fixtures

- `Supervisor` com max_retries=2
- Estados retryáveis: PLAN, TEST_RED, CODE_GREEN
- Estados terminais: SPEC_VALIDATION, SECURITY
- Exceções: RetryableStepError, ReviewRejectedError, RuntimeError genérico
