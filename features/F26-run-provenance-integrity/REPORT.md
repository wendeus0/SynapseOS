# F26 Report

## Resumo executivo

- A F26 foi implementada como endurecimento de provenance minima por run.
- O recorte ficou fechado em `G-06 + G-08`, com `spec_hash`, `initiated_by` e security events reutilizando o schema atual de runs/events.
- O enforcement principal ficou antes do inicio da pipeline: runs pendentes revalidam o hash da SPEC e falham em `REQUEST` se o arquivo for adulterado.

## Escopo entregue

- Evolucao do `RunRecord` com `spec_hash` e `initiated_by`.
- Upgrade local de schema SQLite para bases legadas sem Alembic.
- Hash SHA-256 da SPEC persistido no submit e revalidado no `run_existing()`.
- Novos event types `security_provenance_recorded`, `security_spec_hash_mismatch` e `security_guardrail_triggered`.
- Exposicao de `Spec Hash` e `Initiated By` em `runs show` e no `RUN_REPORT.md`.
- Cobertura unitaria e de integracao para schema legado, tampering de SPEC, guardrail event, rendering e report.

## Validacoes executadas

- Leitura e alinhamento com `CONTEXT.md`, `docs/architecture/SDD.md`, `docs/architecture/TDD.md` e `docs/architecture/SPEC_FORMAT.md`.
- Validacao da SPEC com `validate_spec_file(Path('features/F26-run-provenance-integrity/SPEC.md'))`.
- `uv run --no-sync python -m pytest tests/unit/test_config.py tests/unit/test_persistence.py tests/unit/test_runtime_dispatch.py tests/unit/test_worker_runtime.py tests/unit/test_cli_runs_rendering.py tests/unit/test_report_generator.py tests/integration/test_pipeline_persistence.py tests/integration/test_runs_submit_cli.py tests/integration/test_runs_cli.py tests/integration/test_worker_runtime_flow.py -q`
- `uv run --no-sync ruff check src/aignt_os/security.py src/aignt_os/config.py src/aignt_os/runtime/dispatch.py src/aignt_os/persistence.py src/aignt_os/cli/rendering.py src/aignt_os/reporting.py tests/unit/test_config.py tests/unit/test_persistence.py tests/unit/test_runtime_dispatch.py tests/unit/test_worker_runtime.py tests/unit/test_cli_runs_rendering.py tests/unit/test_report_generator.py tests/integration/test_pipeline_persistence.py tests/integration/test_runs_submit_cli.py tests/integration/test_runs_cli.py tests/integration/test_worker_runtime_flow.py`
- `uv run --no-sync mypy src/aignt_os/security.py src/aignt_os/config.py src/aignt_os/runtime/dispatch.py src/aignt_os/persistence.py src/aignt_os/cli/rendering.py src/aignt_os/reporting.py`
- `./scripts/security-gate.sh`

## Security review

- O review local nao deixou findings bloqueantes no recorte.
- O principal risco da frente era aceitar run pendente com SPEC adulterada; isso foi mitigado com revalidacao do SHA-256 antes de `run_started`, mantendo a falha em `REQUEST`.
- O audit trail adicional permaneceu no canal atual de `run_events`, sem criar superficie paralela e sem reabrir auth ou Alembic.

## Riscos residuais

- Runs legadas sem `spec_hash` continuam executaveis por compatibilidade; elas nao ganham protecao retrospectiva contra tampering.
- `initiated_by` continua sendo uma origem declarativa simples; identidade forte e autorizacao continuam fora desta frente.
- O mapeamento de `security_guardrail_triggered` cobre os guardrails explicitamente reconhecidos hoje e pode ser ampliado em features futuras.

## Proximos passos

- Executar o fluxo Git completo da F26 ate merge e sync final.

## Status final da frente

- `READY_FOR_COMMIT`
