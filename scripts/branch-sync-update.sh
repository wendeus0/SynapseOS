#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_REF="origin/main"
MODE="rebase"
FETCH=1

# Best-effort update only: block obvious unsafe states and immediate conflicts,
# but a later rebase/merge step can still require manual resolution.

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-ref)
      BASE_REF="${2:?missing value for --base-ref}"
      shift 2
      ;;
    --mode)
      MODE="${2:?missing value for --mode}"
      shift 2
      ;;
    --fetch)
      FETCH=1
      shift
      ;;
    --no-fetch)
      FETCH=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$MODE" != "rebase" && "$MODE" != "merge" ]]; then
  echo "Unsupported mode '$MODE'. Use 'rebase' or 'merge'." >&2
  exit 1
fi

if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must run inside a git worktree." >&2
  exit 1
fi

current_branch="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)"

if [[ "$current_branch" == "main" ]]; then
  echo "Branch sync update is blocked on 'main'." >&2
  exit 1
fi

if [[ -n "$(git -C "$ROOT_DIR" status --porcelain)" ]]; then
  echo "Branch sync update requires a clean working tree." >&2
  exit 1
fi

if [[ "$FETCH" -eq 1 ]] && git -C "$ROOT_DIR" remote get-url origin >/dev/null 2>&1; then
  if ! git -C "$ROOT_DIR" fetch origin main --quiet; then
    echo "Failed to fetch origin/main." >&2
    exit 1
  fi
fi

if ! git -C "$ROOT_DIR" rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  echo "Base reference '$BASE_REF' was not found." >&2
  exit 1
fi

read -r behind ahead < <(git -C "$ROOT_DIR" rev-list --left-right --count "$BASE_REF...HEAD")
printf '%s\n' "Branch sync status before update: branch=$current_branch base=$BASE_REF ahead=$ahead behind=$behind mode=$MODE"

if [[ "$behind" -eq 0 ]]; then
  printf '%s\n' "Branch '$current_branch' is not behind $BASE_REF. No update required."
  exit 0
fi

merge_base="$(git -C "$ROOT_DIR" merge-base HEAD "$BASE_REF")"
merge_tree_output="$(git -C "$ROOT_DIR" merge-tree "$merge_base" HEAD "$BASE_REF")"
if grep -q '^<<<<<<< ' <<<"$merge_tree_output"; then
  echo "Branch sync update is not safe enough to start: immediate conflict detected against $BASE_REF." >&2
  exit 1
fi

printf '%s\n' "Best-effort precheck passed: no immediate conflict was detected against $BASE_REF. ${MODE^} can still require manual resolution."

case "$MODE" in
  rebase)
    git -C "$ROOT_DIR" rebase "$BASE_REF"
    ;;
  merge)
    git -C "$ROOT_DIR" merge --no-edit "$BASE_REF"
    ;;
esac

read -r behind ahead < <(git -C "$ROOT_DIR" rev-list --left-right --count "$BASE_REF...HEAD")
printf '%s\n' "Branch sync status after update: branch=$current_branch base=$BASE_REF ahead=$ahead behind=$behind mode=$MODE"
