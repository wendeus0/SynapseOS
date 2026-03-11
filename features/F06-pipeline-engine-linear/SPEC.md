---
id: F06-pipeline-engine-linear
type: feature
summary: Implementar a primeira engine linear do AIgnt-Synapse-Flow com PipelineStep, StepExecutor e PipelineEngine em fake mode até PLAN ou TEST_RED.
workspace: .
inputs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - features/F03-state-machine-mvp/SPEC.md
  - features/F04-parsing-engine-mvp/SPEC.md
  - features/F05-cli-adapter-base/SPEC.md
outputs:
  - pipeline_step_contracts
  - step_executor_contract
  - pipeline_engine_linear
  - fake_mode_pipeline_tests
constraints:
  - manter escopo estritamente na pipeline linear do AIgnt-Synapse-Flow
  - reutilizar a state machine, o SpecValidator e os contratos ja existentes
  - nao implementar persistencia, worker, supervisor ou adapter real
  - nao depender de Docker, rede ou ferramentas externas reais
  - usar fake environment para PLAN e TEST_RED
acceptance_criteria:
  - Existem contratos tipados para PipelineStep, StepExecutionResult e PipelineContext.
  - Existe um StepExecutor com contrato explicito e testavel para steps lineares em fake mode.
  - Existe um PipelineEngine que executa o fluxo minimo ate PLAN ou TEST_RED, usando validacao real da SPEC em SPEC_VALIDATION.
  - A engine bloqueia o fluxo quando a SPEC e invalida antes de avancar para PLAN.
  - Os testes cobrem caminho feliz ate TEST_RED, execucao interrompida em PLAN, bloqueio por SPEC invalida e falha verificavel quando faltar executor para um step exigido.
non_goals:
  - persistir runs, eventos ou artefatos em banco
  - integrar worker, runtime dual ou supervisor
  - chamar tools reais ou adapters reais
  - executar REVIEW, SECURITY ou DOCUMENT dentro desta feature
  - implementar DAG, paralelismo ou retries
dependencies:
  - F02-spec-engine-mvp
  - F03-state-machine-mvp
  - F04-parsing-engine-mvp
  - F05-cli-adapter-base
---

# Contexto

Depois da F05, o projeto ja possui os blocos minimos para subir um nivel de abstracao: validacao de SPEC, state machine linear, parser MVP e adapter base async. O proximo incremento natural do nucleo e ligar esses contratos por meio do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS, em uma pipeline linear pequena e totalmente controlada.

Esta feature deve permanecer restrita a fake mode. O objetivo nao e orquestrar ferramentas reais ainda, e sim introduzir a primeira camada de `PipelineStep`, `StepExecutor` e `PipelineEngine` capaz de validar a SPEC e encadear hand-offs minimos para `PLAN` e `TEST_RED`.

# Objetivo

Entregar a primeira engine linear do AIgnt-Synapse-Flow com:
- contratos tipados de pipeline;
- validacao real da SPEC no step `SPEC_VALIDATION`;
- execucao linear controlada em fake mode;
- hand-off minimo entre `SPEC_VALIDATION`, `PLAN` e `TEST_RED`;
- testes deterministas para a esteira inicial.

# Escopo

## Incluido

- contratos tipados `PipelineStep`, `StepExecutionResult` e `PipelineContext`
- contrato de `StepExecutor` para steps de pipeline
- `PipelineEngine` linear usando a state machine existente
- validacao real da SPEC por `validate_spec_file()` antes de `PLAN`
- suporte a execucao ate `PLAN` ou ate `TEST_RED`
- fake executors para testes e hand-offs em memoria
- testes unitarios da engine e dos contratos da pipeline

## Fora de escopo

- steps reais de `CODE_GREEN`, `REVIEW`, `SECURITY` ou `DOCUMENT`
- persistencia de contexto, run ou artefatos
- chamada de adapters reais, subprocessos reais ou parsing detalhado dentro do executor
- retries, reroute, rollback e supervisor
- integracao com CLI publica para disparar a pipeline

# Requisitos funcionais

1. O sistema deve expor um contrato tipado para representar um step linear da pipeline.
2. O sistema deve expor um contexto tipado em memoria para compartilhar artefatos entre steps.
3. O sistema deve expor um resultado tipado para o executor devolver artefatos estruturados de hand-off.
4. O PipelineEngine deve reutilizar a state machine atual para respeitar a ordem linear do fluxo.
5. O PipelineEngine deve validar a SPEC real no step `SPEC_VALIDATION`.
6. O PipelineEngine nao deve avancar para `PLAN` quando a SPEC for invalida.
7. O PipelineEngine deve permitir parar apos executar `PLAN`.
8. O PipelineEngine deve permitir executar ate `TEST_RED` em fake mode.
9. O PipelineEngine deve falhar de forma verificavel quando um step requerido nao tiver executor configurado.

# Requisitos nao funcionais

- A implementacao deve continuar pequena e adequada a um recorte de 1 a 3 dias.
- Os testes devem ser deterministas e independentes de Docker, rede e ferramentas reais.
- O contexto de hand-off deve permanecer em memoria nesta feature.
- O design deve permitir evolucao futura para mais steps sem reescrita estrutural da engine.

# Casos de erro

- SPEC invalida bloqueando o avanco em `SPEC_VALIDATION`
- executor ausente para `PLAN` ou `TEST_RED`
- pedido de parada em step nao suportado pelo recorte atual
- estado inicial da state machine incompatível com a esteira minima desta feature

# Cenarios verificaveis

## Cenario 1: fluxo feliz ate TEST_RED

- Dado uma SPEC valida
- E executores fake para `PLAN` e `TEST_RED`
- Quando a engine linear for executada ate `TEST_RED`
- Entao a SPEC e validada
- E os steps `PLAN` e `TEST_RED` produzem hand-offs em memoria

## Cenario 2: parada controlada em PLAN

- Dado uma SPEC valida
- E um executor fake para `PLAN`
- Quando a engine for configurada para parar em `PLAN`
- Entao `PLAN` e executado
- E `TEST_RED` nao e chamado

## Cenario 3: bloqueio por SPEC invalida

- Dado uma SPEC invalida
- Quando a engine atingir `SPEC_VALIDATION`
- Entao o fluxo falha antes de avancar para `PLAN`

## Cenario 4: falha por executor ausente

- Dado uma SPEC valida
- E um executor ausente para um step exigido
- Quando a engine precisar executar esse step
- Entao a falha e explicita e verificavel por teste

# Observacoes

Esta feature nao implementa planner real nem writer real de testes. O fake mode existe apenas para exercitar a primeira orquestracao linear do AIgnt-Synapse-Flow. Persistencia, worker, supervisor e runtime mais completo continuam para as features seguintes.
