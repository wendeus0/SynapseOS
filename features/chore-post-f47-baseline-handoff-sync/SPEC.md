---
id: chore-post-f47-baseline-handoff-sync
type: chore
summary: Sincronizar handoff e backlog ao baseline real apos as merges de F41, F43, F44, F45 e F47.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - docs/IDEAS.md
  - README.md
  - CHANGELOG.md
  - PENDING_LOG.md
  - memory.md
  - tests/unit/test_auth_registry_docs.py
outputs:
  - post_f47_baseline_handoff_sync
  - updated_auth_and_tui_docs_for_current_main
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente a docs, handoff e testes documentais; sem alteracao funcional em src/"
  - "nao introduzir nova feature de produto, nova automacao operacional, Docker ou ADR"
  - "nao reabrir backlog local/residente de auth nem promover transporte remoto a requisito atual"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de boot, build, persistencia pratica em container ou integracao real"
acceptance_criteria:
  - "Existe `features/chore-post-f47-baseline-handoff-sync/SPEC.md` valida descrevendo a frente como chore doc-only de alinhamento pos-`F47`."
  - "`memory.md` e `PENDING_LOG.md` deixam de tratar `F41`, `F43`, `F44`, `F45` e `F47` como apenas drafts/estado implícito e passam a refletir essas merges como baseline atual."
  - "`docs/IDEAS.md` passa a registrar que o recorte local de auth ja absorveu a fundacao (`F29`/`F30`), a abstracao de provider (`F44`), o bucket residente local (`F32`/`F34`/`F35`/`F36`) e o RBAC local (`F47`), mantendo somente `remote_multi_host_auth` como pendencia explicita."
  - "`README.md` documenta o uso atual de `aignt auth init|issue --role ...` e os boundaries de `viewer`, `operator` e `admin` sem sugerir auth remota."
  - "`CHANGELOG.md` ganha uma secao `Unreleased` curta e coerente com o baseline atual, cobrindo TUI, robustez de runtime e RBAC local."
  - "`tests/unit/test_auth_registry_docs.py` trava o novo estado de `docs/IDEAS.md` e `README.md`."
non_goals:
  - "alterar codigo de producao, persistencia, runtime, auth ou dashboard"
  - "reescrever `RUN_REPORT.md` raiz como changelog do repositório"
  - "abrir follow-up funcional para F40, F42, F46 ou auth remota"
  - "mudar workflow de CI, scripts operacionais ou fluxo de merge"
dependencies:
  - F41-dashboard-artifacts-explorer
  - F43-runtime-robustness
  - F44-auth-backend-abstraction
  - F45-tui-performance-optimization
  - F47-advanced-rbac
---

# Contexto

O baseline atual de `origin/main` ja absorveu as merges de `F41`, `F43`, `F44`, `F45`
e `F47`, mas o handoff duravel ainda para no estado pos-`F37`/`F39`. Isso deixa
`memory.md`, `PENDING_LOG.md`, `docs/IDEAS.md`, `README.md` e `CHANGELOG.md`
parcialmente desalinhados do que a CLI e o backlog realmente fazem hoje.

Como o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS e nao
houve nova frente de produto aprovada, o menor recorte util agora e uma chore doc-only
para consolidar esse baseline antes da proxima `technical-triage`.

# Objetivo

Sincronizar handoff, backlog e documentacao publica ao estado real pos-`F47`, sem mudar
comportamento de produto e sem reabrir backlog local/residente ja absorvido.

# Escopo

## Incluido

- criar os artefatos da chore (`SPEC.md`, `NOTES.md`, `CHECKLIST.md`, `REPORT.md`)
- atualizar `memory.md` e `PENDING_LOG.md`
- atualizar `docs/IDEAS.md` apenas no recorte de auth/guardrails afetado pelas merges recentes
- atualizar `README.md` apenas na documentacao publica do auth registry local
- atualizar `CHANGELOG.md` com um resumo curto do baseline atual
- ajustar o teste documental de `README.md`/`docs/IDEAS.md`

## Fora de escopo

- qualquer mudanca em `src/`
- revalidacao pratica com Docker
- nova SPEC de produto
- reabertura de `remote_multi_host_auth`, `F40`, `F42` ou `F46`

# Requisitos nao funcionais

- a frente deve permanecer pequena, reversivel e auditavel
- a memoria duravel deve registrar estado estavel, nao historico detalhado de conversa
- a documentacao publica nao pode prometer auth remota, provider externo pronto ou TUI distribuida

# Casos de erro

- `memory.md` continuar tratando `F41`, `F43`, `F44`, `F45` e `F47` como apenas drafts
- `docs/IDEAS.md` continuar descrevendo `G-11` sem `F44` e `F47`
- `README.md` continuar omitindo o uso atual de `--role`
- `CHANGELOG.md` continuar parando na release `0.1.0` sem registrar o baseline atual
- o teste documental continuar travando o estado pre-`F47`

# Cenarios verificaveis

## Cenario 1: handoff deixa de parar na F39/F37

- Dado `memory.md` e `PENDING_LOG.md` atualizados
- Quando o estado atual do repositório for consultado
- Entao ambos refletem que `main` ja incorpora `F41`, `F43`, `F44`, `F45` e `F47`
- E a proxima decisao volta a ser uma nova `technical-triage` apos esta chore

## Cenario 2: backlog de auth reflete o baseline local atual

- Dado `docs/IDEAS.md` atualizado
- Quando o item `G-11` for lido
- Entao ele registra `F44` como abstracao local do provider e `F47` como RBAC local absorvido
- E continua deixando apenas `remote_multi_host_auth` explicitamente adiado

## Cenario 3: README documenta o fluxo publico atual de roles

- Dado `README.md` atualizado
- Quando a secao `Auth Registry Local` for lida
- Entao ela mostra `aignt auth init|issue --role ...`
- E delimita `viewer`, `operator` e `admin` sem sugerir auth remota ou distribuida

# Observacoes

`RUN_REPORT.md` na raiz continua tratado como artefato de execucao, nao como handoff
canonico do baseline. O fechamento desta frente deve ficar em
`features/chore-post-f47-baseline-handoff-sync/REPORT.md`.
