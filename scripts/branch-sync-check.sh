#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_REF="origin/main"
FETCH=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-ref)
      BASE_REF="${2:?missing value for --base-ref}"
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

if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must run inside a git worktree." >&2
  exit 1
fi

current_branch="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)"

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

printf '%s\n' "Branch sync status: branch=$current_branch base=$BASE_REF ahead=$ahead behind=$behind"

if [[ "$behind" -gt 0 ]]; then
  echo "Branch '$current_branch' is behind $BASE_REF." >&2
  exit 1
fi

exit 0
