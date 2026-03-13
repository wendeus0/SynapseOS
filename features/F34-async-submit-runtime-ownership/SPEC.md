---
id: F34-async-submit-runtime-ownership
type: feature
summary: Exigir ownership compativel do runtime residente para `runs submit` autenticado quando o dispatch resolver para `async`.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - features/F15-public-run-submission/SPEC.md
  - features/F29-auth-rbac-foundation/SPEC.md
  - features/F32-runtime-resident-principal-binding/SPEC.md
  - src/aignt_os/cli/app.py
  - src/aignt_os/runtime/dispatch.py
  - src/aignt_os/runtime/service.py
outputs:
  - async_dispatch_runtime_ownership_gate
  - async_submit_auth_red_tests
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente ao dispatch autenticado de `runs submit`; sem mudar socket, IPC, transporte remoto ou auth registry"
  - "preservar compatibilidade quando `auth_enabled=false`"
  - "preservar fallback compativel para estado legado do runtime sem `started_by`"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de Docker, build, boot em container ou integracao externa"
acceptance_criteria:
  - "Quando `auth_enabled=false`, `runs submit --mode async` e `--mode auto` preservam o comportamento atual."
  - "Quando `auth_enabled=true` e `runs submit` resolver para `sync`, o comando preserva o comportamento autenticado atual."
  - "Quando `auth_enabled=true` e `runs submit` resolver para `async`, a submissao falha com `Environment error:` se nao houver runtime residente em estado `running`."
  - "Quando `auth_enabled=true`, `runs submit` resolver para `async` e o runtime residente tiver `started_by`, a submissao falha com `Authorization error:` se o principal autenticado for diferente do principal que iniciou o runtime."
  - "Quando `auth_enabled=true`, `runs submit` resolver para `async` e o runtime residente estiver `running` em estado legado sem `started_by`, o fallback compativel atual continua permitindo a submissao."
  - "Existe cobertura unitaria e de integracao para `--mode async`, `--mode auto` resolvido para `async`, mismatch de principal e fallback legado."
non_goals:
  - "alterar o auth registry local ou introduzir binding por `token_id`"
  - "mudar o comportamento de `runs submit` sincrono"
  - "alterar o worker para enforcement posterior de ownership"
  - "abrir transporte autenticado entre processos ou hosts"
dependencies:
  - F15-public-run-submission
  - F29-auth-rbac-foundation
  - F32-runtime-resident-principal-binding
---

# Contexto

Depois da `F29` e da `F30`, `runs submit` ja exige auth local quando ela estiver
habilitada. Depois da `F32`, o runtime residente local passou a persistir `started_by`
como o principal autenticado que o iniciou, sem abrir socket nem transporte novo. O
AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS.

Mesmo assim, o caminho autenticado de `runs submit` ainda aceita dispatch assinado como
`async` sem verificar se o runtime residente disponivel pertence ao mesmo principal.
Esse gap permite enfileirar runs para processamento assinado por um runtime iniciado por
outro operador ou ate mesmo sem runtime residente pronto quando auth local estiver ativa.

# Objetivo

Endurecer `runs submit` autenticado somente quando o dispatch resolver para `async`,
exigindo runtime residente local compativel com o principal autenticado sem alterar o
caminho sincrono nem ampliar o recorte para transporte novo.

# Escopo

## Incluido

- gate de ownership para `runs submit` autenticado quando o dispatch resolver para `async`
- tratamento distinto para ausencia de runtime residente pronto versus mismatch de principal
- reutilizacao do binding `started_by` ja entregue pela `F32`
- fallback compativel para runtime legado sem `started_by`
- testes unitarios do dispatch e testes de integracao da CLI autenticada

## Fora de escopo

- qualquer alteracao no worker ou na ordem de processamento de runs pendentes
- binding por `token_id` ou novas roles alem de `viewer|operator`
- qualquer alteracao em `runtime start|status|stop`
- socket, IPC, RPC ou operacao remota/multi-host

# Casos de erro

- `runs submit --mode async` autenticado sem runtime residente em `running`
- `runs submit --mode async` autenticado com runtime residente iniciado por outro principal
- `runs submit --mode auto` autenticado resolvendo para `async` com runtime ownership incompativel
- estado do runtime inconsistente, que nao deve ser tratado como pronto para async

# Cenarios verificaveis

## Cenario 1: auth desabilitada preserva baseline

- Dado `auth_enabled=false`
- Quando `runs submit --mode async` ou `runs submit --mode auto` for executado
- Entao o comportamento atual permanece inalterado

## Cenario 2: async autenticado exige runtime residente pronto

- Dado `auth_enabled=true` e um principal `operator-user`
- Quando `runs submit --mode async` for executado sem runtime residente em `running`
- Entao a CLI retorna `Environment error:`
- E nenhuma run nova e persistida

## Cenario 3: async autenticado exige o mesmo principal

- Dado `auth_enabled=true`, um runtime residente iniciado por `operator-a` e um principal `operator-b`
- Quando `runs submit --mode async` ou `--mode auto` resolvido para `async` for executado por `operator-b`
- Entao a CLI retorna `Authorization error:`
- E nenhuma run nova e persistida

## Cenario 4: fallback legado permanece compativel

- Dado `auth_enabled=true` e um runtime residente valido sem `started_by`
- Quando `runs submit --mode async` for executado por um principal `operator`
- Entao a run continua sendo enfileirada com sucesso

# Observacoes

Esta frente fecha apenas o ownership gap no submit autenticado para o runtime residente
local. Ela nao tenta resolver ownership diferido no worker nem o bucket maior de
`resident_transport_auth`.
