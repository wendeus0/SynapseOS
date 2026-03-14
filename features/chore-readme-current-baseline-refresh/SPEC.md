---
id: chore-readme-current-baseline-refresh
type: chore
summary: Atualizar o README publicado no GitHub para refletir o baseline tecnico atual do projeto.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - README.md
  - memory.md
  - docs/operations/LIFECYCLE.md
  - tests/unit/test_public_onboarding_docs.py
  - tests/unit/test_release_readiness_docs.py
  - tests/unit/test_watch_and_cancellation_docs.py
outputs:
  - refreshed_readme_current_baseline
  - updated_doc_regression_tests_for_github_readme
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "restringir a frente a documentacao e testes documentais; sem alteracao funcional em src/"
  - "tratar o README como snapshot tecnico atual do repositorio, nao como historico do roadmap"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de boot, build, persistencia pratica em container ou integracao real"
acceptance_criteria:
  - "Existe `features/chore-readme-current-baseline-refresh/SPEC.md` valida descrevendo a revisao do README como chore doc-only."
  - "`README.md` deixa de ancorar o estado atual do projeto em `F18`/`F22` e passa a descrever explicitamente o baseline pos-`F23 -> F47`."
  - "`README.md` passa a listar a superficie publica atual da CLI, incluindo `runs watch`, `runs cancel`, lifecycle do runtime e auth local."
  - "`README.md` referencia `docs/operations/LIFECYCLE.md` como manual operacional detalhado e preserva os boundaries locais atuais (sem auth remota, sem scheduler/fila remota, sem operacao distribuida)."
  - "Os testes documentais travam o novo snapshot tecnico do README e continuam cobrindo quickstart, preview, watch/cancel e auth local."
non_goals:
  - "alterar codigo de producao, runtime, TUI, auth ou persistencia"
  - "reescrever CHANGELOG, memory.md ou backlog operacional"
  - "abrir nova feature de produto ou retomar roadmap historico no README"
dependencies:
  - chore-post-f40-f42-baseline-sync
---

# Contexto

O `README.md` publicado no GitHub esta sincronizado com `main`, mas ainda mistura
snapshot atual com narrativa historica de MVP e etapa 2. Isso faz a pagina inicial
do repositorio continuar parecendo ancorada em `F18`/`F22`, apesar de `main` ja
incorporar guardrails pos-release, auth local com RBAC, ownership local do runtime,
dashboard TUI, cancelamento local e robustez adicional do runtime.

Como o AIgnt-Synapse-Flow continua sendo a engine propria de pipeline do AIgnt OS e
nao ha mudanca funcional aprovada, o menor recorte util agora e uma chore doc-only
para transformar o README em um retrato tecnico fiel do baseline atual.

# Objetivo

Atualizar o `README.md` para funcionar como snapshot tecnico atual do repositorio,
refletindo a superficie publica vigente da CLI, o baseline operacional corrente e os
boundaries locais do projeto sem reabrir narrativa antiga de roadmap.

# Escopo

## Incluido

- criar os artefatos da chore (`SPEC.md`, `NOTES.md`, `CHECKLIST.md`, `REPORT.md`)
- reescrever trechos desatualizados do `README.md`
- ajustar testes documentais do README

## Fora de escopo

- qualquer mudanca em `src/`
- reescrita de `CHANGELOG.md`, `memory.md` ou `PENDING_LOG.md`
- edicao de release notes historicas

# Requisitos nao funcionais

- o README deve ficar mais curto e mais factual, com foco em contribuidores e operadores
- o texto deve privilegiar capacidades atuais e boundaries reais, nao cronologia de features
- a documentacao publica nao pode sugerir auth remota, cancelamento distribuido ou web UI

# Casos de erro

- o README continuar sugerindo que a proxima frente ainda e pos-`F22`
- o README continuar listando apenas features antigas e omitindo capacidades atuais do runtime
- o README continuar sem mostrar a superficie publica atual de `runs watch`, `runs cancel`, lifecycle e auth local

# Cenarios verificaveis

## Cenario 1: pagina inicial descreve o baseline atual

- Dado o `README.md` atualizado
- Quando um leitor abrir a pagina principal do repositorio
- Entao ele encontra um resumo tecnico do baseline atual pos-`F23 -> F47`
- E nao precisa inferir o estado do projeto a partir de listas antigas de roadmap

## Cenario 2: superficie publica atual fica explicita

- Dado o `README.md` atualizado
- Quando a documentacao publica da CLI for lida
- Entao ela lista `runs submit/show/list/watch/cancel`, lifecycle do runtime e auth local
- E preserva os boundaries locais atuais

## Cenario 3: regressao documental fica coberta

- Dado a suite documental ajustada
- Quando os testes do README forem executados
- Entao eles travam quickstart, preview, watch/cancel, auth local e o novo snapshot tecnico

# Observacoes

`docs/operations/LIFECYCLE.md` continua sendo o manual operacional detalhado. O README
deve apontar para ele e concentrar-se no retrato atual de alto nivel do repositorio.
