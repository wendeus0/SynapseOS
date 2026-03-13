---
id: F31-g11-remote-auth-decomposition
type: chore
summary: Decompor formalmente o residual remoto de G-11 em backlog executavel sem iniciar implementacao de transporte ou auth remota.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - PENDING_LOG.md
  - memory.md
  - features/F29-auth-rbac-foundation/SPEC.md
  - features/F30-auth-registry-cli/SPEC.md
  - src/aignt_os/auth.py
  - src/aignt_os/runtime/service.py
outputs:
  - g11_remote_backlog_decomposition
  - post_baseline_handoff_alignment
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "trabalhar apenas a decomposicao documental do residual de G-11"
  - "nao alterar o comportamento atual de CLI, runtime, auth local ou persistencia"
  - "nao introduzir socket, IPC autenticado, transporte em rede, RBAC novo ou coordenacao entre hosts"
  - "nao exigir DOCKER_PREFLIGHT, porque a frente nao depende de Docker, build de imagem ou runtime em container"
acceptance_criteria:
  - "Existe `features/F31-g11-remote-auth-decomposition/SPEC.md` valida, com o residual de `G-11` decomposto explicitamente em fundacao local absorvida, transporte autenticado residente ainda pendente e operacao remota/multi-host adiada."
  - "`docs/IDEAS.md` deixa de descrever `G-11` como um backlog monolitico apenas de `socket + RBAC` e passa a refletir a absorcao local em `F29`/`F30` e o residual remoto de forma decomposta."
  - "`PENDING_LOG.md` registra que, apos a estabilizacao da baseline pela `#66`, a frente ativa voltou a ser backlog de produto e a tarefa imediata e decompor formalmente `G-11` antes de qualquer codigo novo."
  - "`memory.md` passa a refletir que `main` esta estavel, que nao ha feature de produto implementando transporte remoto agora e que a proxima decisao codificavel depende de uma SPEC pequena derivada do bucket `resident_transport_auth`."
  - "Existe cobertura de documentacao travando o novo estado de `docs/IDEAS.md` para `G-11`, mantendo `F29` e `F30` como absorcoes da fundacao local."
non_goals:
  - "implementar transporte autenticado entre CLI e runtime residente"
  - "abrir operacao remota, multi-host, TCP, TLS ou qualquer transporte em rede"
  - "introduzir novos contratos Pydantic, schema SQLite ou migracoes"
  - "reabrir follow-up local de auth ja coberto por `F29` e `F30`"
dependencies:
  - F29-auth-rbac-foundation
  - F30-auth-registry-cli
  - chore-repo-checks-baseline-restore
---

# Contexto

Depois da `F29-auth-rbac-foundation` e da `F30-auth-registry-cli`, o baseline atual do
AIgnt OS ja possui auth local opt-in na borda da CLI e lifecycle local do registry de
tokens. O AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS,
mas o runtime atual segue estritamente local: processo residente leve, arquivo de
estado local e nenhuma camada de socket, IPC autenticado ou operacao entre hosts.

Com a baseline restaurada pela chore `repo-checks` pos-`#66`, o unico residual
explicito da `IDEA-001` voltou a ser `G-11`. Porem, esse residual ainda aparece no
backlog como um bloco vago de "socket + RBAC", grande demais para virar implementacao
segura no baseline atual sem nova ambiguidade de escopo.

# Objetivo

Decompor formalmente o residual remoto de `G-11` em backlog executavel, registrando o
que ja foi absorvido localmente, o que ainda depende de futura SPEC pequena e o que
permanece explicitamente adiado fora do baseline atual.

# Escopo

## Incluido

- criar uma SPEC curta e validavel para a frente `F31`
- alinhar `docs/IDEAS.md` ao novo estado de `G-11`
- alinhar `PENDING_LOG.md` e `memory.md` ao baseline pos-`#66`
- adicionar cobertura de documentacao para travar a decomposicao de `G-11`

## Fora de escopo

- qualquer implementacao de socket, IPC, RPC ou transporte em rede
- qualquer alteracao em `src/aignt_os/auth.py` ou no runtime
- novas roles, policy engine ou RBAC distribuido
- rotacao distribuida, revogacao entre hosts ou descoberta remota do runtime

# Decomposicao obrigatoria de G-11

`G-11` passa a ser tratado com tres buckets explicitos:

1. `local_cli_auth`
   - ja absorvido em `F29` e `F30`
   - cobre auth local opt-in na CLI, roles `viewer|operator` e lifecycle local do registry
2. `resident_transport_auth`
   - ainda pendente
   - representa o futuro recorte pequeno para autenticar interacoes entre a CLI e um runtime residente local
   - nao esta sendo implementado nesta frente
3. `remote_multi_host_auth`
   - explicitamente adiado
   - cobre operacao entre hosts, transporte em rede, revogacao distribuida e qualquer coordenacao remota

# Requisitos nao funcionais

- a frente deve caber em uma sessao curta e permanecer doc-only
- nenhuma decisao nova desta frente pode contradizer `F29`, `F30` ou o runtime atual
- a decomposicao deve reduzir ambiguidade, nao abrir nova arquitetura
- se surgir necessidade real de ADR para o bucket `resident_transport_auth`, isso deve
  ser registrado como bloqueio futuro e nao resolvido nesta frente

# Casos de erro

- documentacao continuar insinuando que auth remota ja existe no baseline atual
- `G-11` permanecer descrito como backlog monolitico sem bucketizacao
- handoff continuar apontando baseline instavel mesmo apos a chore `#66`

# Cenarios verificaveis

## Cenario 1: backlog deixa de tratar G-11 como bloco unico

- Dado o baseline pos-`F30` e pos-`#66`
- Quando `docs/IDEAS.md` for lido
- Entao `G-11` aparece como residual decomposto
- E `F29`/`F30` continuam reconhecidas como absorcao da fundacao local

## Cenario 2: handoff reflete baseline estavel

- Dado `main` estabilizada apos a chore de `repo-checks`
- Quando `PENDING_LOG.md` e `memory.md` forem lidos
- Entao a frente ativa registrada volta a ser backlog de produto
- E nenhuma implementacao de transporte remoto e tratada como trabalho em curso

# Observacoes

Esta frente encerra apenas a ambiguidade do backlog. O proximo trabalho de codigo,
quando existir, deve nascer de uma SPEC pequena derivada do bucket
`resident_transport_auth`, mantendo o baseline local-first e sem reabrir auth remota
por inercia.
