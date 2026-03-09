# Test-Driven Development Strategy — AIgnt OS v3

## 1. Objetivo
Definir a estratégia de testes para implementar o AIgnt OS com foco em confiabilidade do **AIgnt-Synapse-Flow**, a engine própria de pipeline do projeto, dos adapters CLI, do formato de SPEC, do runtime dual (CLI + worker leve) e dos hand-offs entre etapas.

## 2. Princípios
- Validar `DOCKER_PREFLIGHT` antes de iniciar execução prática da feature.
- Testar contratos antes da implementação.
- Separar testes de unidade, integração, pipeline e worker.
- Simular ferramentas CLI com outputs realistas.
- Validar hand-offs entre steps, não apenas comportamento interno.
- Garantir que o AIgnt-Synapse-Flow permaneça refatorável.
- Fazer `TEST_RED` derivar testes da SPEC validada, não do prompt cru.
- Tratar `SECURITY_REVIEW` como gate antes de `REPORT` e `COMMIT`.

---

## 3. Fluxo de execução por feature

```text
DOCKER_PREFLIGHT → SPEC → TEST_RED → CODE_GREEN → REFACTOR → SECURITY_REVIEW → REPORT → COMMIT
```

- `DOCKER_PREFLIGHT` é executado pela skill `repo-automation`.
- O `DOCKER_PREFLIGHT` padrão em CI e no fluxo local deve ser leve, sem `docker compose up`.
- O runtime completo deve ser validado em workflow dedicado ou por acionamento explícito.
- `SPEC` só avança com ambiente validado.
- `SECURITY_REVIEW` fecha o ciclo técnico antes de `REPORT` e `COMMIT`.

## 4. Estratégia RED → GREEN → REFACTOR

### RED
Escrever primeiro testes para:
- transições de estado,
- parsing,
- validação da SPEC,
- comportamento dos adapters,
- decisões do supervisor,
- persistência de run,
- comportamento do worker,
- geração do `RUN_REPORT.md`.

### GREEN
Implementar o mínimo necessário para cada contrato passar.

### REFACTOR
Extrair abstrações estáveis:
- `PipelineStep`,
- `StepExecutor`,
- `RunRepository`,
- `SupervisorDecision`,
- `SpecValidator`,
- `ArtifactStore`.

---

## 5. Níveis de Teste

### 5.1 Unit tests
Cobrem:
- limpeza de output,
- extração de blocos,
- validação da SPEC,
- transições da state machine,
- classificação de falhas,
- serialização de modelos,
- geração do `RUN_REPORT.md`,
- validação do `DOCKER_PREFLIGHT`,
- checagens do gate de segurança,
- regras de lock de run.

### 5.2 Integration tests
Cobrem:
- spec engine + schema,
- adapter + parser,
- pipeline manager + supervisor,
- persistência de run,
- CLI + AIgnt-Synapse-Flow,
- worker + repositório de runs.

### 5.3 CLI simulation tests
Simulam subprocessos e ferramentas reais usando `stdout`, `stderr`, `returncode` e timeout falsos.

### 5.4 Pipeline tests
Executam o fluxo ponta a ponta com ambiente fake, incluindo:
- invalidar SPEC,
- reprovar review,
- falhar em security,
- reroute por falha de ferramenta,
- geração de artifacts.

### 5.5 Worker tests
Verificam:
- polling de runs pendentes,
- lock de execução,
- retries longos,
- retomada de run,
- marcação de falha terminal,
- não duplicação de processamento.

### 5.6 Contract tests
Garantem que:
- todos os adapters implementam o contrato mínimo,
- todos os steps devolvem `StepResult` válido,
- toda SPEC válida atende ao schema oficial.

---

## 6. Ordem Recomendada de Implementação
1. `DOCKER_PREFLIGHT` validado pela skill `repo-automation`.
2. SPEC aprovada.
3. Modelos Pydantic principais.
4. Validador da SPEC híbrida.
5. State machine.
6. Cleaner/parser básico.
7. Base adapter async.
8. Step executor.
9. AIgnt-Synapse-Flow linear.
10. Persistência SQLite.
11. Worker leve.
12. Supervisor com retry/reroute.
13. Geração do `RUN_REPORT.md`.
14. Adapters reais.
15. Paralelismo controlado.

---

## 7. Estratégia de Mocking
- Mock de subprocess assíncrono.
- Fixtures com stdout realista das ferramentas.
- Snapshots de outputs ruidosos.
- Fixtures para SPEC válida e inválida.
- Repositórios em memória para testes rápidos.
- Artefatos temporários em diretório isolado por teste.

---

## 8. Casos de Teste Prioritários

### 8.1 Preflight e segurança
- `test_docker_preflight_requires_valid_compose_config()`
- `test_docker_preflight_blocks_feature_execution_when_environment_is_invalid()`
- `test_security_review_gate_runs_before_report_and_commit()`
- `test_security_gate_rejects_insecure_operational_patterns()`

### 8.2 Parsing
- `test_cli_output_cleaning()`
- `test_parser_extracts_python_code_block()`
- `test_parser_rejects_corrupted_output()`
- `test_parser_removes_ansi_sequences()`

### 8.3 SPEC
- `test_spec_yaml_header_is_required()`
- `test_spec_schema_validation_passes_for_valid_spec()`
- `test_spec_validation_blocks_plan_when_invalid()`
- `test_spec_requires_acceptance_criteria()`

### 8.4 State machine / pipeline
- `test_state_machine_transitions()`
- `test_invalid_transition_raises_error()`
- `test_pipeline_rolls_back_from_review_to_code_green()`
- `test_pipeline_stops_on_unrecoverable_security_failure()`
- `test_pipeline_does_not_advance_without_valid_spec()`

### 8.5 Adapters
- `test_cli_timeout_handling()`
- `test_cli_nonzero_exit_code()`
- `test_adapter_sanitizes_ansi_sequences()`
- `test_all_adapters_return_cli_execution_result()`

### 8.6 Supervisor
- `test_pipeline_failure_recovery()`
- `test_supervisor_reroutes_after_repeated_failures()`
- `test_supervisor_marks_terminal_failure_after_schema_error()`
- `test_supervisor_requests_retry_after_timeout()`

### 8.7 Worker
- `test_worker_picks_pending_run()`
- `test_worker_respects_run_lock()`
- `test_worker_requeues_retryable_step()`
- `test_worker_generates_run_report_after_completion()`
- `test_worker_does_not_process_completed_run()`

### 8.8 Persistência e relatório
- `test_run_repository_persists_current_state()`
- `test_artifact_store_saves_raw_and_clean_outputs()`
- `test_run_report_contains_steps_tools_and_failures()`

---

## 9. Fixtures Recomendadas
```text
tests/
  fixtures/
    docker/
      valid_compose_config.txt
      invalid_compose_config.txt
    cli_outputs/
      gemini_plan.txt
      codex_tests.txt
      opencode_code.txt
      claude_review.txt
      noisy_mixed_output.txt
    specs/
      valid_feature_spec.md
      invalid_missing_yaml_spec.md
      invalid_acceptance_criteria_spec.md
    reports/
      expected_run_report.md
```

---

## 10. Estrutura de Testes Sugerida
```text
tests/
  unit/
    test_docker_preflight.py
    test_spec_validator.py
    test_parsing_cleaners.py
    test_state_machine.py
    test_retry_policy.py
    test_report_generator.py
    test_security_gate.py
  integration/
    test_adapter_parser_flow.py
    test_pipeline_memory_flow.py
    test_cli_pipeline_entrypoint.py
  pipeline/
    test_happy_path.py
    test_failure_recovery.py
    test_review_rework.py
  worker/
    test_worker_runtime.py
    test_worker_locking.py
  fixtures/
    ...
```

---

## 11. Critérios de Qualidade
A suíte deve garantir:
- hand-offs confiáveis,
- validação rígida da SPEC,
- previsibilidade do AIgnt-Synapse-Flow,
- worker seguro para retries longos,
- `DOCKER_PREFLIGHT` executável e verificável,
- `SECURITY_REVIEW` funcionando como gate,
- relatórios de execução reproduzíveis,
- confiança para refatoração contínua.

## 12. Critérios de Saída do MVP
O MVP só deve ser considerado tecnicamente pronto quando houver testes cobrindo:
- bloqueio da feature quando `DOCKER_PREFLIGHT` falhar,
- SPEC inválida bloqueando a esteira,
- timeout de ferramenta,
- reroute básico,
- retorno de `REVIEW` para `CODE_GREEN`,
- gate de segurança antes de `REPORT`/`COMMIT`,
- run longa em worker,
- geração de `RUN_REPORT.md`.
