# RUN_REPORT — {run_id}

## Resumo da run

- **Status**: completed
- **Estado final**: DOCUMENT
- **Initiated By**: local_cli
- **Spec Hash**: abc123
- **SPEC ID**: F06-pipeline-engine-linear
- **SPEC Summary**: Implementar a primeira engine linear do AIgnt-Synapse-Flow

## Estados percorridos

| Estado | Status | Ferramenta | Return code | Duração (ms) | Timeout |
|---|---|---|---|---|---|
| SPEC_VALIDATION | completed | - | - | - | - |
| PLAN | completed | fake-executor | 0 | 45 | no |
| DOCUMENT | completed | - | - | - | - |

## Eventos relevantes

- `security_provenance_recorded` @ `REQUEST`: Provenance recorded for initiated_by=local_cli spec_hash=abc123.
- `run_started` @ `REQUEST`: Run started at REQUEST.
- `step_completed` @ `SPEC_VALIDATION`: Step SPEC_VALIDATION completed.
- `step_completed` @ `PLAN`: Step PLAN completed.
- `run_completed` @ `DOCUMENT`: Run completed at DOCUMENT.

## Falhas e retries

Nenhuma falha registrada nesta execução.

## Artefatos gerados

- `artifacts/{run_id}/PLAN/plan_md.txt`
- `artifacts/{run_id}/SPEC_VALIDATION/spec_id.txt`
- `artifacts/{run_id}/SPEC_VALIDATION/spec_summary.txt`
