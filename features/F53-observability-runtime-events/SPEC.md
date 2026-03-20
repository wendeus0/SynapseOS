---
id: F53-observability-runtime-events
type: feature
summary: "Enriquecer a timeline local do Synapse-Flow com eventos operacionais explícitos de contexto, step e transição"
inputs:
  - Runtime events já persistidos em run_events
  - RunContext e workspace_path introduzidos em F51 e F52
outputs:
  - Timeline persistida com eventos operacionais mais explícitos
  - CLI e RUN_REPORT capazes de refletir melhor o contexto da run
  - Cobertura de teste para os novos eventos e seu consumo
acceptance_criteria:
  - O sistema deve persistir um evento explícito de contexto operacional da run antes da execução útil dos steps
  - O sistema deve persistir quando um step do runtime começa e quando a pipeline avança de estado
  - Os novos eventos devem reaproveitar run_events, sem exigir nova infraestrutura de observabilidade
  - runs show e RUN_REPORT devem continuar legíveis e incorporar os novos sinais sem regressão da saída atual
  - Deve existir cobertura de teste unitária e de integração para a timeline enriquecida
non_goals:
  - Introduzir tracing distribuído, OTEL ou backend remoto
  - Criar streaming em tempo real fora da observabilidade local já existente
  - Alterar a CLI pública para um modelo desktop-first
  - Criar sistema genérico de métricas ou alertas ativos
---

# Contexto
O SynapseOS já persiste `run_started`, `step_completed`, `run_completed`, `run_failed`, `supervisor_decision` e alguns eventos específicos de segurança ou ownership. Isso é suficiente para auditoria mínima, mas ainda deixa lacunas na explicação operacional da timeline.

Depois da `F51-runtime-boundaries-foundation` e da `F52-workspace-isolation-foundation`, o sistema já conhece melhor o contexto da run: `initiated_by`, `workspace_path`, `spec_path` e o `RunContext` efetivo. O próximo passo lógico é tornar essa informação visível na timeline local do Synapse-Flow, a engine própria de pipeline do SynapseOS, sem abrir nova stack de observabilidade.

Hoje, quando um operador inspeciona uma run, ainda faltam sinais explícitos para responder rapidamente:

1. qual contexto operacional foi inicializado para aquela run;
2. quando um step efetivamente começou;
3. quando a pipeline mudou de estado entre etapas.

# Objetivo
Enriquecer a timeline persistida da run com eventos operacionais explícitos e consistentes, reaproveitando `run_events`.

O recorte desta feature deve:

1. registrar um evento de contexto operacional da run;
2. registrar o início de cada step útil;
3. registrar transições de estado da pipeline;
4. refletir esses sinais na CLI atual e no `RUN_REPORT.md` sem romper a legibilidade existente.
