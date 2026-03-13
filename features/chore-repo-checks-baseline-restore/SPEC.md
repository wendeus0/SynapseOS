---
id: chore-repo-checks-baseline-restore
type: chore
summary: Restaurar o repo-checks na baseline atual corrigindo a divida de ruff format e alinhando o handoff pos-F30.
inputs:
  - CONTEXT.md
  - docs/architecture/SDD.md
  - docs/architecture/TDD.md
  - docs/architecture/SPEC_FORMAT.md
  - scripts/commit-check.sh
  - .github/workflows/operational-ci.yml
  - PENDING_LOG.md
  - ERROR_LOG.md
  - memory.md
outputs:
  - repo_checks_green
  - post_f30_handoff_sync
constraints:
  - "manter o AIgnt-Synapse-Flow como a engine propria de pipeline do AIgnt OS"
  - "corrigir apenas a divida confirmada de formatacao e o handoff pos-F30"
  - "nao alterar workflow, scripts operacionais ou contrato publico da CLI"
  - "nao introduzir nova feature de produto, auth remota ou qualquer recorte de G-11"
  - "nao exigir DOCKER_PREFLIGHT porque a frente nao depende de Docker, build de imagem ou runtime em container"
acceptance_criteria:
  - "`uv run --no-sync ruff format --check .` fecha verde na branch da chore."
  - "`./scripts/commit-check.sh --sync-dev --skip-branch-validation --skip-docker --skip-security` fecha verde, restaurando paridade local com o job `repo-checks`."
  - "A correcao de baseline fica restrita aos 6 arquivos apontados pelo `ruff format --check .`, sem delta funcional fora de formatacao."
  - "`PENDING_LOG.md`, `ERROR_LOG.md` e `memory.md` refletem o estado pos-F30 e o incidente operacional da PR `#65`."
  - "Existe `REPORT.md` curto e auditavel consolidando a restauracao do gate e os riscos residuais."
non_goals:
  - "relaxar ou redefinir o `repo-checks` no workflow"
  - "abrir nova feature de produto"
  - "alterar codigo de producao fora do ajuste de formatacao"
  - "reabrir backlog de socket, auth remota ou qualquer item de G-11"
dependencies:
  - F30-auth-registry-cli
---

# Contexto

A `F30-auth-registry-cli` foi mergeada em `main`, mas a PR `#65` precisou de merge explicito porque o job `repo-checks` continuou falhando por uma divida de `ruff format --check .` em 6 arquivos fora do diff funcional da feature. O baseline atual segue estavel em comportamento, mas o gate operacional principal de repositório nao pode continuar dependendo de excecao manual.

Ao mesmo tempo, `PENDING_LOG.md`, `ERROR_LOG.md` e `memory.md` ainda refletem um estado anterior a `F30` e a esse incidente operacional. O menor recorte util agora e restaurar o gate e sincronizar o handoff, sem abrir escopo novo de produto.

# Objetivo

Restaurar o `repo-checks` na baseline atual corrigindo a divida confirmada de formatacao e alinhar os artefatos de handoff ao estado pos-F30.

# Escopo

## Incluido

- aplicacao de `ruff format` apenas nos 6 arquivos atualmente fora do padrao
- revalidacao local do caminho equivalente ao `repo-checks`
- alinhamento de `PENDING_LOG.md`, `ERROR_LOG.md` e `memory.md`
- `NOTES.md`, `CHECKLIST.md` e `REPORT.md` proprios da chore

## Fora de escopo

- mudanca em workflow CI
- alteracao de `commit-check.sh`
- nova feature de produto
- refatoracao funcional em `src/`

# Observacoes

Se a revalidacao local mostrar um segundo bloqueio real alem da formatacao confirmada, ele deve ser registrado no `ERROR_LOG.md` e triado separadamente, sem ampliar esta chore automaticamente.
