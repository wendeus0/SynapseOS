---
id: F03-state-machine-mvp
type: feature
summary: Modelar a state machine minima do AIgnt-Synapse-Flow com estados principais da pipeline e validacao explicita de transicoes validas e invalidas no MVP.
workspace: .
inputs:
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - decision_on_official_pipeline_states
outputs:
  - state_machine_contract
  - explicit_state_enum_or_equivalent
  - valid_transition_rules
  - invalid_transition_failures
constraints:
  - manter o recorte apenas na modelagem de estados e transicoes
  - nao implementar supervisor, retries ou reroute
  - nao executar pipeline completa nem acoplar adapters reais
  - preservar o fluxo linear state-driven do MVP
acceptance_criteria:
  - Existe uma representacao explicita dos estados principais da pipeline do MVP.
  - Existem transicoes validas explicitamente suportadas entre os estados definidos para esta feature.
  - Transicoes invalidas falham de forma verificavel.
  - O fluxo nao avanca para PLAN sem passar por SPEC_VALIDATION.
  - Existe estado terminal de sucesso e ao menos um estado terminal de falha para o recorte do MVP.
  - Os testes da feature cobrem happy path minimo e pelo menos um conjunto de transicoes invalidas.
non_goals:
  - implementar step executor
  - executar handoff real entre etapas
  - integrar supervisor, retry ou reroute
  - integrar worker, persistencia ou adapter CLI
  - modelar DAG ou paralelismo
dependencies:
  - F02-spec-engine-mvp
---

# Contexto

O AIgnt OS adota o AIgnt-Synapse-Flow como a engine propria de pipeline do projeto, e essa engine depende de uma modelagem state-driven auditavel. A arquitetura ja define os estados principais no SDD, mas ainda falta o primeiro incremento executavel dessa state machine para validar transicoes do fluxo do MVP.

Depois da F02, que entrega a validacao minima da SPEC, o proximo passo natural do nucleo e explicitar os estados e as regras de transicao sem antecipar executor de passos, supervisor ou pipeline completa.

# Objetivo

Entregar a state machine minima do MVP com:
- representacao explicita dos estados principais da pipeline;
- transicoes validas entre os estados cobertos pela feature;
- rejeicao verificavel de transicoes invalidas;
- garantia de que `PLAN` nao seja alcancado sem `SPEC_VALIDATION`;
- estados terminais minimos de sucesso e falha.

# Escopo

## Incluido

- estados principais do fluxo interno do MVP:
  - `REQUEST`
  - `SPEC_DISCOVERY`
  - `SPEC_NORMALIZATION`
  - `SPEC_VALIDATION`
  - `PLAN`
  - `TEST_RED`
  - `CODE_GREEN`
  - `REVIEW`
  - `SECURITY`
  - `DOCUMENT`
  - `COMPLETE`
  - `FAILED`
- transicoes lineares validas entre esses estados
- falha explicita para transicao invalida
- contrato minimo para consultar o estado atual
- testes unitarios de transicoes validas e invalidas

## Fora de escopo

- `RETRYING`
- logica de retry
- reroute
- supervisor
- acoplamento com steps reais
- persistencia da state machine
- execucao de pipeline ponta a ponta

# Requisitos funcionais

1. O sistema deve representar explicitamente os estados principais do AIgnt-Synapse-Flow no MVP.
2. O estado inicial da run deve permitir entrada controlada no fluxo a partir de `REQUEST`.
3. O sistema deve permitir a progressao linear do macrofluxo interno:
   `REQUEST -> SPEC_DISCOVERY -> SPEC_NORMALIZATION -> SPEC_VALIDATION -> PLAN -> TEST_RED -> CODE_GREEN -> REVIEW -> SECURITY -> DOCUMENT -> COMPLETE`.
4. O sistema deve impedir transicao direta que pule `SPEC_VALIDATION` antes de `PLAN`.
5. O sistema deve impedir transicoes fora da ordem definida nesta feature.
6. O sistema deve permitir transicao para `FAILED` a partir de pelo menos um estado ativo do fluxo.
7. O sistema deve expor erro verificavel quando uma transicao invalida for solicitada.

# Requisitos nao funcionais

- A implementacao deve permanecer pequena o suficiente para 1 a 3 dias.
- A modelagem deve ser explicita e facil de auditar.
- O contrato deve ser compativel com extensao futura para retries e rollback sem exigir reescrita total.
- A feature nao deve introduzir dependencias pesadas alem da stack ja definida no projeto.

# Casos de erro

- tentativa de ir para `PLAN` sem passar por `SPEC_VALIDATION`
- tentativa de pular de `REQUEST` direto para `TEST_RED`
- tentativa de avancar apos `COMPLETE`
- tentativa de transicao a partir de estado terminal invalido para o recorte atual

# Cenarios verificaveis

## Cenario 1: happy path minimo

- Dado que a state machine inicia no estado inicial do fluxo
- Quando as transicoes validas sao executadas em ordem
- Entao o estado final alcançado e `COMPLETE`

## Cenario 2: bloqueio antes de PLAN

- Dado que a run ainda nao passou por `SPEC_VALIDATION`
- Quando uma transicao para `PLAN` e solicitada fora da ordem
- Entao a state machine falha de forma verificavel

## Cenario 3: transicao invalida arbitraria

- Dado um estado ativo qualquer do fluxo
- Quando uma transicao nao suportada e solicitada
- Entao a state machine retorna erro verificavel

## Cenario 4: falha terminal

- Dado um estado ativo do fluxo
- Quando a run e marcada como falha no recorte suportado
- Entao o estado terminal `FAILED` e alcançado

# Observacoes

Esta feature modela apenas a state machine minima do AIgnt-Synapse-Flow, a engine propria de pipeline do AIgnt OS. Ela nao executa steps reais nem decide retry, reroute ou rollback; esses comportamentos ficam para features posteriores.
