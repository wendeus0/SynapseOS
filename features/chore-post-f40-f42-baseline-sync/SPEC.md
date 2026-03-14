---
id: chore-post-f40-f42-baseline-sync
type: chore
summary: Sincronizar handoff e documentacao publica ao baseline real apos as merges de F40 e F42.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - README.md
  - CHANGELOG.md
  - memory.md
  - PENDING_LOG.md
  - ERROR_LOG.md
  - features/F40-local-cancellation/SPEC.md
  - features/F42-tui-filters/SPEC.md
outputs:
  - post_f40_f42_baseline_sync
  - updated_public_docs_for_watch_and_cancel
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente a docs, handoff e testes documentais; sem alteracao funcional em src/"
  - "nao reabrir cancelamento distribuido, scheduler remoto, auth remota ou TUI fora do baseline ja mergeado"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de boot, build, persistencia pratica em container ou integracao real"
acceptance_criteria:
  - "Existe `features/chore-post-f40-f42-baseline-sync/SPEC.md` valida descrevendo a frente como chore doc-only de alinhamento pos-`F40`/`F42`."
  - "`features/F40-local-cancellation/` e `features/F42-tui-filters/` passam a ter `NOTES.md`, `CHECKLIST.md` e `REPORT.md`, refletindo exatamente o baseline ja mergeado."
  - "`memory.md` e `PENDING_LOG.md` deixam de tratar `F40` e `F42` como recortes apenas no archive branch e passam a refletir essas merges como baseline atual de `main`."
  - "`ERROR_LOG.md` registra que a PR `#87` entrou com delta misto alem do recorte funcional da `F40`, e que a mitigacao aplicada foi uma chore de sync/handoff."
  - "`README.md` documenta `aignt runs watch <run_id>`, `aignt runs cancel <run_id>` e os atalhos reais `Enter`, `a`, `f`, `r`, `x` e `k`, deixando claro que o cancelamento atual e apenas local e gracioso."
  - "`CHANGELOG.md` ganha um `Unreleased` coerente com o baseline atual, incluindo filtros no dashboard TUI e cancelamento local de runs."
  - "Existe cobertura documental automatizada travando a superficie publica atual de watch/cancel e a presenca dos artefatos retrocompletados de `F40` e `F42`."
non_goals:
  - "alterar codigo de producao, persistencia, runtime, TUI ou auth"
  - "reescrever `RUN_REPORT.md` raiz como changelog do repositorio"
  - "abrir nova feature de produto apos `F40`/`F42`"
  - "introduzir cancelamento distribuido, kill forcado de subprocessos ou fila remota"
dependencies:
  - F40-local-cancellation
  - F42-tui-filters
---

# Contexto

`origin/main` ja absorveu `F42-tui-filters` pela PR `#86` e `F40-local-cancellation`
pela PR `#87`, mas o handoff duravel ainda descreve um estado pre-merge e continua
tratando esses recortes como backlog apenas no archive branch. Alem disso, as duas
features ficaram sem `NOTES.md`, `CHECKLIST.md` e `REPORT.md`, e o `README.md` ainda
nao documenta a superficie publica atual do dashboard TUI e do cancelamento local.

Como o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS e
nao houve aprovacao para nova frente de produto, o menor recorte util agora e uma
chore doc-only para consolidar esse baseline antes da proxima `technical-triage`.

# Objetivo

Sincronizar handoff, backlog e documentacao publica ao estado real pos-`F40`/`F42`,
sem mudar comportamento de produto e sem ampliar o escopo funcional ja mergeado.

# Escopo

## Incluido

- criar os artefatos da chore (`SPEC.md`, `NOTES.md`, `CHECKLIST.md`, `REPORT.md`)
- retrocompletar `NOTES.md`, `CHECKLIST.md` e `REPORT.md` de `F40` e `F42`
- atualizar `memory.md`, `PENDING_LOG.md` e `ERROR_LOG.md`
- atualizar `README.md` no recorte publico de `runs watch` e `runs cancel`
- atualizar `CHANGELOG.md` com o baseline atual
- adicionar cobertura documental automatizada

## Fora de escopo

- qualquer mudanca em `src/`
- revalidacao pratica com Docker
- nova SPEC de produto
- limpeza estrutural da PR `#87` alem do registro documental objetivo

# Requisitos nao funcionais

- a frente deve permanecer pequena, reversivel e auditavel
- os artefatos retroativos de `F40` e `F42` devem descrever o que entrou em `main`, nao reinterpretar escopo
- a documentacao publica nao pode prometer cancelamento distribuido, fila remota ou kill forcado de subprocessos

# Casos de erro

- `memory.md` ou `PENDING_LOG.md` continuarem tratando `F40`/`F42` como backlog fora da fila ativa
- `README.md` continuar omitindo `aignt runs cancel <run_id>` ou os atalhos reais do dashboard
- `CHANGELOG.md` continuar sem mencionar filtros TUI ou cancelamento local
- `F40` e `F42` continuarem sem artefatos minimos de encerramento

# Cenarios verificaveis

## Cenario 1: handoff deixa de parar antes de F40 e F42

- Dado `memory.md` e `PENDING_LOG.md` atualizados
- Quando o estado atual do repositorio for consultado
- Entao ambos refletem que `main` ja incorpora `F40` e `F42`
- E a proxima decisao volta a ser uma nova `technical-triage` apos esta chore

## Cenario 2: README passa a refletir watch, filtros e cancelamento locais

- Dado `README.md` atualizado
- Quando a documentacao publica for lida
- Entao ela mostra `aignt runs watch <run_id>` e `aignt runs cancel <run_id>`
- E ela delimita que o cancelamento atual e apenas local e gracioso

## Cenario 3: F40 e F42 ficam auditaveis como features ja concluídas

- Dado os diretorios `features/F40-local-cancellation/` e `features/F42-tui-filters/`
- Quando os artefatos da feature forem inspecionados
- Entao cada diretorio contem `SPEC.md`, `NOTES.md`, `CHECKLIST.md` e `REPORT.md`
- E esses artefatos descrevem o baseline ja mergeado sem abrir trabalho novo

# Observacoes

`RUN_REPORT.md` na raiz continua tratado como artefato de execucao, nao como handoff
canonico do baseline. O fechamento desta frente deve ficar em
`features/chore-post-f40-f42-baseline-sync/REPORT.md`.
