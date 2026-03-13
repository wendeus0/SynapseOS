---
id: F37-post-f36-g11-sync
type: chore
summary: Alinhar backlog e handoff ao estado real do baseline apos F34, F35 e F36.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - PENDING_LOG.md
  - memory.md
  - features/F33-post-f32-handoff-sync/SPEC.md
  - features/F34-async-submit-runtime-ownership/SPEC.md
  - features/F35-worker-runtime-ownership-filter/SPEC.md
  - features/F36-worker-owner-skip-observability/SPEC.md
outputs:
  - post_f36_g11_alignment
  - updated_g11_local_vs_remote_baseline_docs
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente a docs e handoff; sem alteracao funcional de CLI, runtime, auth ou persistencia"
  - "nao introduzir nova feature de produto, transporte remoto, socket, IPC ou ADR"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de Docker, build, boot ou integracao pratica"
acceptance_criteria:
  - "Existe `features/F37-post-f36-g11-sync/SPEC.md` valida descrevendo a frente como chore doc-only de alinhamento pos-`F36`."
  - "`docs/IDEAS.md` deixa de descrever `G-11` como apenas 'primeiro slice residente absorvido' e passa a registrar que o bucket residente local foi absorvido por `F32`, `F34`, `F35` e `F36`, mantendo somente a operacao remota/multi-host como pendencia explicita."
  - "`memory.md` passa a refletir que `main` incorpora `F34`, `F35` e `F36`, deixa de tratar `resident_transport_auth` como bucket local ainda aberto e aponta a `F37` como frente doc-only imediata."
  - "`PENDING_LOG.md` registra a merge de `F34`, `F35` e `F36`, a absorcao local de `resident_transport_auth` e a abertura da `F37` para fechar o drift documental antes da proxima triagem."
  - "A cobertura em `tests/unit/test_auth_registry_docs.py` trava explicitamente o novo estado pos-`F36` em `docs/IDEAS.md`."
non_goals:
  - "implementar novo comportamento de worker, dispatch, runtime ou auth remota"
  - "abrir novo slice funcional de `resident_transport_auth`"
  - "iniciar `remote_multi_host_auth` ou qualquer coordenacao entre hosts"
dependencies:
  - F33-post-f32-handoff-sync
  - F34-async-submit-runtime-ownership
  - F35-worker-runtime-ownership-filter
  - F36-worker-owner-skip-observability
---

# Contexto

A `F33-post-f32-handoff-sync` alinhou o baseline ao estado pos-`F32`, quando o bucket
`resident_transport_auth` ainda tinha apenas o primeiro slice concreto absorvido. Depois
disso, `main` incorporou a `F34`, a `F35` e a `F36`, fechando ownership local no submit,
no consumo da fila pelo worker e na observabilidade do skip. O AIgnt-Synapse-Flow
continua sendo a engine propria de pipeline do AIgnt OS, e nenhuma frente de transporte
remoto ou multi-host foi iniciada.

Apesar disso, a documentacao central e o handoff duravel ainda pararam antes dessas
features: `docs/IDEAS.md`, `memory.md`, `PENDING_LOG.md` e o teste documental ainda
tratam `G-11` como se houvesse apenas um primeiro slice residente absorvido.

# Objetivo

Realinhar backlog e handoff ao estado real pos-`F36`, deixando explicito que o bucket
residente local de `G-11` foi absorvido no baseline atual e que o residual aberto da
IDEA ficou restrito a operacao remota/multi-host.

# Escopo

## Incluido

- criar a SPEC e os artefatos minimos da `F37`
- atualizar `docs/IDEAS.md` para refletir a absorcao local de `resident_transport_auth`
- atualizar `memory.md` e `PENDING_LOG.md` para o estado pos-`F36`
- ajustar o teste documental que trava o contrato atual de `docs/IDEAS.md`

## Fora de escopo

- qualquer implementacao nova em `src/`
- alteracao de README, workflow, CI ou scripts operacionais
- qualquer novo contrato de auth remota ou transporte entre hosts

# Requisitos nao funcionais

- a frente deve permanecer doc-only
- o delta deve ser pequeno, auditavel e sem comportamento de produto novo
- a documentacao resultante nao pode sugerir que auth remota ja exista
- a memoria duravel deve registrar apenas estado estavel e recomendacao imediata

# Casos de erro

- `docs/IDEAS.md` continuar descrevendo `G-11` como se apenas a `F32` tivesse sido absorvida
- `memory.md` continuar apontando `resident_transport_auth` como bucket local ainda indefinido
- `PENDING_LOG.md` continuar bloqueando a proxima triagem no handoff pos-`F32`
- o teste documental continuar travando o estado antigo de `G-11`

# Cenarios verificaveis

## Cenario 1: backlog de G-11 fica alinhado ao pos-F36

- Dado `docs/IDEAS.md` atualizado
- Quando o item `G-11` for lido
- Entao ele registra `F29` e `F30` como fundacao local absorvida
- E registra `F32`, `F34`, `F35` e `F36` como absorcao do bucket residente local
- E continua deixando `remote_multi_host_auth` explicitamente adiado

## Cenario 2: handoff duravel para de parar na F32

- Dado `memory.md` e `PENDING_LOG.md` atualizados
- Quando o baseline atual for consultado
- Entao ambos refletem que `main` ja incorpora `F34`, `F35` e `F36`
- E apontam a `F37` apenas como sync documental antes da proxima triagem

# Observacoes

Esta frente nao declara `G-11` totalmente encerrada, porque o bucket remoto continua fora
do baseline atual. Ela apenas fecha o recorte local/residente e evita que a triagem
seguinte reabra trabalho ja absorvido.
