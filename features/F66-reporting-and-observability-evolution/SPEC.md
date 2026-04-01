---
id: F66-reporting-and-observability-evolution
type: feature
summary: Enhanced run reports with structured metadata, execution timeline, adapter performance metrics, and structured error summaries.
status: draft
created: 2026-03-31
owner: agent
inputs: []
outputs: []
acceptance_criteria:
    - RunReport includes execution_timeline with state transitions and durations
    - RunReport includes adapter_metrics with per-adapter success rates and avg durations
    - RunReport includes structured_errors list with error categories and counts
    - RunReport includes feature_id and feature_title from SPEC metadata
    - RunReport JSON schema is validated against a JSON Schema spec
    - Unit tests verify all new report fields are populated correctly
    - Existing reporting tests continue to pass
non_goals: []
---

# Contexto

O `RunReport` atual em `reporting.py` é um arquivo Markdown simples (RUN_REPORT.md). Ele não tem:

- Timeline de execução com transições de estado e durações
- Métricas por adapter (success rate, avg duration)
- Estrutura de erros categorizados
- Validação via JSON Schema
- Campos de feature_id e feature_title

# Decisão

Expandir o sistema de relatórios para incluir:

1. **Structured timeline** — lista de transições de estado com timestamp e duration desde a transição anterior.
2. **Adapter metrics** — por adapter: total calls, success count, failure count, avg duration ms, categorização de erros.
3. **Structured errors** — lista de erros categorizados com type, message, step, e count.
4. **Feature metadata** — campos `feature_id` e `feature_title` populados do frontmatter da SPEC.
5. **JSON Schema validation** — o report é primeiramente gerado como Pydantic model, depois renderizado para Markdown.

O `RunReport` existente continua como Pydantic model; adicionamos novos campos.

# Escopo

## Dentro do Escopo

- `ExecutionTimeline` e `TimelineEntry` Pydantic models
- `AdapterMetrics` Pydantic model
- `StructuredError` Pydantic model
- Campos `execution_timeline`, `adapter_metrics`, `structured_errors`, `feature_id`, `feature_title` no `RunReport`
- `generate_structured_report(run_id, run_record)` helper que popula todos os campos
- Unit tests em `tests/unit/test_reporting_evolution.py`

## Fora do Escopo

- Alteração do formato de renderização Markdown existente (mantemos compatibilidade)
- Integração com sistema de eventos externo

# Arquivos

- `src/synapse_os/reporting.py` — adicionar models e campos ao `RunReport`
- `tests/unit/test_reporting_evolution.py` — unit tests
