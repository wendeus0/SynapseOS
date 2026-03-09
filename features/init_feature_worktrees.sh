#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./scripts/init_feature_worktrees.sh /caminho/para/repo [base-branch]
# Exemplo:
#   ./scripts/init_feature_worktrees.sh ~/code/aignt-os main

REPO_PATH="${1:-.}"
BASE_BRANCH="${2:-main}"
WORKTREE_ROOT="${REPO_PATH%/}/../aignt-os-worktrees"

FEATURES=(
  "feature/f01-bootstrap-contracts:F01-bootstrap-contracts"
  "feature/f02-spec-engine-mvp:F02-spec-engine-mvp"
  "feature/f03-state-machine-mvp:F03-state-machine-mvp"
  "feature/f04-parsing-engine-mvp:F04-parsing-engine-mvp"
  "feature/f05-cli-adapter-base:F05-cli-adapter-base"
  "feature/f06-pipeline-engine-linear:F06-pipeline-engine-linear"
  "feature/f07-persistence-artifacts:F07-persistence-artifacts"
  "feature/f08-worker-runtime-dual:F08-worker-runtime-dual"
  "feature/f09-supervisor-mvp:F09-supervisor-mvp"
  "feature/f10-run-report-one-real-adapter:F10-run-report-one-real-adapter"
)

mkdir -p "$WORKTREE_ROOT"
cd "$REPO_PATH"

git fetch origin || true

for ITEM in "${FEATURES[@]}"; do
  BRANCH="${ITEM%%:*}"
  DIRNAME="${ITEM##*:}"
  TARGET="$WORKTREE_ROOT/$DIRNAME"

  if [ -d "$TARGET/.git" ] || [ -f "$TARGET/.git" ]; then
    echo "[skip] worktree já existe: $TARGET"
    continue
  fi

  echo "[create] $BRANCH -> $TARGET"
  git worktree add -b "$BRANCH" "$TARGET" "$BASE_BRANCH"

  mkdir -p "$TARGET/features/$DIRNAME"
  cat > "$TARGET/features/$DIRNAME/SPEC.md" <<'SPEC'
---
id: replace-me
type: feature
summary: Descreva a feature em uma frase.
workspace: .
inputs:
  - user_request
outputs:
  - implementation
constraints:
  - python
  - cli-first
acceptance_criteria:
  - definir
non_goals: []
security_notes: []
---

## 1. Contexto

## 2. Objetivo

## 3. Escopo

## 4. Fora de Escopo

## 5. Regras Funcionais

## 6. Casos de Erro

## 7. Critérios de Aceite Detalhados

## 8. Artefatos Esperados

## 9. Observações para Planejamento

## 10. Observações para Revisão
SPEC

  touch "$TARGET/features/$DIRNAME/NOTES.md"
done

echo "\nWorktrees criados em: $WORKTREE_ROOT"
