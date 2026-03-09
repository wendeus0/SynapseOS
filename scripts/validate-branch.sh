#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_REF="origin/main"
FETCH=0
ALLOW_MAIN=0

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
    --allow-main)
      ALLOW_MAIN=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$FETCH" -eq 1 ]] && git -C "$ROOT_DIR" remote get-url origin >/dev/null 2>&1; then
  if ! git -C "$ROOT_DIR" fetch origin main --quiet; then
    echo "Warning: failed to fetch origin/main, using local refs only." >&2
  fi
fi

if ! git -C "$ROOT_DIR" rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  if [[ "$BASE_REF" == "origin/main" ]] && git -C "$ROOT_DIR" rev-parse --verify main >/dev/null 2>&1; then
    BASE_REF="main"
  else
    echo "Base reference '$BASE_REF' was not found." >&2
    exit 1
  fi
fi

current_branch="$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)"

if [[ "$current_branch" == "main" && "$ALLOW_MAIN" -ne 1 ]]; then
  echo "Direct operational flow on 'main' is blocked. Use a feature branch." >&2
  exit 1
fi

base_sha="$(git -C "$ROOT_DIR" rev-parse "$BASE_REF")"
head_sha="$(git -C "$ROOT_DIR" rev-parse HEAD)"

if [[ "$base_sha" == "$head_sha" ]]; then
  printf '%s\n' "Branch aligned with $BASE_REF at $head_sha"
  exit 0
fi

read -r behind ahead < <(git -C "$ROOT_DIR" rev-list --left-right --count "$BASE_REF...HEAD")

if ! git -C "$ROOT_DIR" merge-base --is-ancestor "$BASE_REF" HEAD; then
  echo "Current branch is not aligned with $BASE_REF. behind=$behind ahead=$ahead" >&2
  exit 1
fi

printf '%s\n' "Branch aligned with $BASE_REF. behind=$behind ahead=$ahead"
