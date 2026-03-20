# RUN_REPORT — {run_id}

## Resumo da run

- **Status**: completed
- **Estado final**: DOCUMENT
- **Initiated By**: local_cli
- **Workspace Path**: {workspace_path}
- **Spec Hash**: abc123
- **SPEC ID**: F06-pipeline-engine-linear
- **SPEC Summary**: Implementar a primeira engine linear do Synapse-Flow

## Estados percorridos

| Estado | Status | Ferramenta | Return code | Duração (ms) | Timeout |
|---|---|---|---|---|---|
| SPEC_VALIDATION | completed | - | - | - | - |
| PLAN | completed | fake-executor | 0 | 45 | no |
| DOCUMENT | completed | - | - | - | - |

## Eventos relevantes

- `security_provenance_recorded` @ `REQUEST`: Provenance recorded for initiated_by=local_cli spec_hash=abc123.
- `run_context_initialized` @ `REQUEST`: Run context initialized for initiated_by=local_cli workspace={workspace_path}.
- `run_started` @ `REQUEST`: Run started at REQUEST. workspace={workspace_path}
- `state_transitioned` @ `REQUEST`: REQUEST -> SPEC_VALIDATION
- `step_started` @ `SPEC_VALIDATION`: Step SPEC_VALIDATION started.
- `step_completed` @ `SPEC_VALIDATION`: Step SPEC_VALIDATION completed.
- `state_transitioned` @ `SPEC_VALIDATION`: SPEC_VALIDATION -> PLAN
- `step_started` @ `PLAN`: Step PLAN started.
- `step_completed` @ `PLAN`: Step PLAN completed.
- `run_completed` @ `DOCUMENT`: Run completed at DOCUMENT.

## Falhas e retries

Nenhuma falha registrada nesta execução.

## Artefatos gerados

- `artifacts/{run_id}/PLAN/plan_md.txt`
- `artifacts/{run_id}/SPEC_VALIDATION/spec_id.txt`
- `artifacts/{run_id}/SPEC_VALIDATION/spec_summary.txt`
