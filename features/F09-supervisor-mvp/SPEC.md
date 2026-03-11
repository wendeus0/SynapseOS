---
id: F09-supervisor-mvp
type: feature
summary: Adicionar um supervisor deterministico ao runtime linear para suportar retry, reroute simples e rework de review no AIgnt-Synapse-Flow.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - features/F08-worker-runtime-dual/SPEC.md
outputs:
  - supervisor_module
  - extended_pipeline_steps
  - supervisor_tests
constraints:
  - manter o AIgnt-Synapse-Flow como engine propria de pipeline do AIgnt OS
  - manter a pipeline linear e state-driven no MVP
  - nao introduzir heuristica aberta, memoria semantica decisoria ou multiplos workers
  - nao gerar RUN_REPORT.md nesta feature
  - nao integrar adapter real nesta feature
acceptance_criteria:
  - Existe um `SupervisorDecision` deterministico capaz de decidir entre `advance`, `retry`, `reroute`, `return_to_code_green` e `fail`.
  - O `PipelineEngine` suporta execucao ate `CODE_GREEN`, `REVIEW` e `SECURITY`.
  - Uma falha recuperavel em `PLAN`, `TEST_RED` ou `CODE_GREEN` pode gerar retry limitado do mesmo step.
  - Falhas repetidas em um step com executor alternativo configurado podem gerar reroute deterministico.
  - Rejeicao em `REVIEW` retorna a execucao para `CODE_GREEN`.
  - Falha de `SPEC_VALIDATION` encerra a run como falha terminal sem retry.
  - Falha em `SECURITY` encerra a run como falha terminal sem reroute.
  - Existe pelo menos um teste cobrindo a persistencia de eventos de decisao do supervisor em uma run.
non_goals:
  - scheduler distribuido
  - retries longos entre multiplos polls do worker
  - adapters reais
  - geracao de RUN_REPORT.md
  - supervisor baseado em memoria semantica
dependencies:
  - F08-worker-runtime-dual
---

# Contexto

A F08 conectou persistencia operacional e runtime dual, permitindo que o worker leve consuma runs pendentes do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS. O gap restante do MVP nao esta mais na fila simples nem no lock local. O gap esta no comportamento da pipeline quando um step falha, quando uma revisao pede retrabalho e quando existe mais de um executor possivel para o mesmo step.

O repositório ja documenta esse recorte no `TDD.md` e nos testes de rework/failure recovery, mas a implementacao atual ainda para em `TEST_RED` e trata falha como terminal imediata. A F09 fecha esse degrau com um supervisor pequeno, deterministico e explicitamente limitado ao MVP.

# Objetivo

Entregar o primeiro supervisor do MVP, com regras deterministicas e integracao minima ao runtime linear:

- expandir a pipeline ate `CODE_GREEN`, `REVIEW` e `SECURITY`;
- decidir retry limitado para falhas recuperaveis;
- rerotear para executor alternativo quando retries se esgotarem e houver rota configurada;
- devolver a execucao para `CODE_GREEN` quando `REVIEW` reprovar;
- registrar as decisoes do supervisor de forma auditavel na persistencia da run.

# Escopo

## Incluido

- modulo de supervisor com contrato explicito de decisao
- suporte de pipeline para `CODE_GREEN`, `REVIEW` e `SECURITY`
- retries limitados no mesmo ciclo de execucao
- reroute simples com executores alternativos explicitamente configurados
- rework `REVIEW -> CODE_GREEN`
- eventos persistidos para decisoes do supervisor
- testes unitarios, de pipeline e de persistencia para o recorte

## Fora de escopo

- resumir ou retomar retries entre restarts do runtime
- multiprocessamento de workers
- heuristica adaptativa baseada em memoria
- `DOCUMENT`, `RUN_REPORT.md` e adapter real ponta a ponta
- nova CLI publica para inspecionar decisoes do supervisor

# Requisitos funcionais

1. O sistema deve expor um contrato de decisao do supervisor para falhas e rework.
2. O supervisor deve permitir `retry` limitado para falhas recuperaveis em `PLAN`, `TEST_RED` e `CODE_GREEN`.
3. O supervisor deve permitir `reroute` quando o limite de retry for excedido e existir executor alternativo configurado.
4. O supervisor deve retornar a execucao para `CODE_GREEN` quando `REVIEW` for rejeitado.
5. O supervisor deve falhar terminalmente em `SPEC_VALIDATION`.
6. O supervisor deve falhar terminalmente em `SECURITY`.
7. A pipeline deve conseguir executar ate `SECURITY` no caminho feliz desta feature.
8. A persistencia deve registrar cada decisao do supervisor como evento auditavel.

# Requisitos nao funcionais

- As decisoes devem ser deterministicas e pequenas.
- O recorte deve permanecer linear, sem DAG e sem coordenação distribuida.
- A implementacao deve preservar compatibilidade com a persistencia e o worker da F08.
- O worker pode continuar single-process e single-workspace.
- O comportamento deve ser validavel sem depender de adapter real nem de Docker.

# Casos de erro

- SPEC invalida
- step sem executor configurado
- falha recuperavel que excede o limite de retries sem rota alternativa
- reroute solicitado sem executor alternativo valido
- revisao reprovada repetidamente
- gate de seguranca reprovado

# Cenarios verificaveis

## Cenario 1: retry de falha recuperavel

- Dado um step `CODE_GREEN` com falha recuperavel
- Quando o numero de tentativas ainda estiver abaixo do limite
- Entao o supervisor decide `retry`
- E a pipeline reexecuta o mesmo step

## Cenario 2: reroute apos retries esgotados

- Dado um step `TEST_RED` com falhas recuperaveis repetidas
- E um executor alternativo configurado
- Quando o limite de retries for atingido
- Entao o supervisor decide `reroute`
- E a pipeline executa o step usando a rota alternativa

## Cenario 3: review reprova e pede retrabalho

- Dado que `CODE_GREEN` ja foi executado com sucesso
- Quando `REVIEW` reprova o resultado
- Entao o supervisor decide `return_to_code_green`
- E a pipeline retorna para `CODE_GREEN`

## Cenario 4: falha terminal de security

- Dado um step `SECURITY` com erro ou reprovação
- Quando a execucao falha nesse step
- Entao o supervisor decide `fail`
- E a run termina como `failed`

# Observacoes

Esta feature entrega apenas o supervisor MVP. Retry persistido entre polls, relatorio final de run, adapters reais e qualquer supervisor heuristico ficam para frentes posteriores.
