#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALLOW_MAIN=0
SKIP_BRANCH_VALIDATION=0
SKIP_FORMAT=0
SKIP_LINT=0
SKIP_TYPECHECK=0
SKIP_TESTS=0
SKIP_DOCKER=0
SKIP_SECURITY=0
FETCH=0
BASE_REF="origin/main"
BUILD_IMAGE=0
FULL_RUNTIME=0
HOOK_MODE=0
FLOW_MODE="sync-dev"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.cache/uv}"
mkdir -p "$UV_CACHE_DIR"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-main)
      ALLOW_MAIN=1
      shift
      ;;
    --hook-mode)
      HOOK_MODE=1
      shift
      ;;
    --sync-dev)
      FLOW_MODE="sync-dev"
      shift
      ;;
    --no-sync)
      FLOW_MODE="no-sync"
      shift
      ;;
    --skip-branch-validation)
      SKIP_BRANCH_VALIDATION=1
      shift
      ;;
    --skip-format)
      SKIP_FORMAT=1
      shift
      ;;
    --skip-lint)
      SKIP_LINT=1
      shift
      ;;
    --skip-typecheck)
      SKIP_TYPECHECK=1
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=1
      shift
      ;;
    --skip-docker)
      SKIP_DOCKER=1
      shift
      ;;
    --skip-security)
      SKIP_SECURITY=1
      shift
      ;;
    --fetch)
      FETCH=1
      shift
      ;;
    --base-ref)
      BASE_REF="${2:?missing value for --base-ref}"
      shift 2
      ;;
    --build-image)
      BUILD_IMAGE=1
      shift
      ;;
    --full-runtime)
      FULL_RUNTIME=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$HOOK_MODE" -eq 1 ]]; then
  SKIP_DOCKER=1
  FLOW_MODE="no-sync"
fi

if [[ "$SKIP_BRANCH_VALIDATION" -ne 1 ]]; then
  branch_args=(--base-ref "$BASE_REF")
  if [[ "$ALLOW_MAIN" -eq 1 ]]; then
    branch_args+=(--allow-main)
  fi
  if [[ "$FETCH" -eq 1 ]]; then
    branch_args+=(--fetch)
  else
    branch_args+=(--no-fetch)
  fi
  "$ROOT_DIR/scripts/validate-branch.sh" "${branch_args[@]}"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to run repository checks." >&2
  exit 1
fi

if [[ "$FLOW_MODE" == "sync-dev" ]]; then
  uv sync --locked --extra dev
  uv_run_args=(run)
  flow_description="uv sync --locked --extra dev + uv run"
else
  uv_run_args=(run --no-sync)
  flow_description="uv run --no-sync"
fi

printf '%s\n' "Resolved local validation flow: $flow_description"

if [[ "$SKIP_FORMAT" -ne 1 ]]; then
  uv "${uv_run_args[@]}" ruff format --check .
fi

if [[ "$SKIP_LINT" -ne 1 ]]; then
  uv "${uv_run_args[@]}" ruff check .
fi

if [[ "$SKIP_TYPECHECK" -ne 1 ]]; then
  uv "${uv_run_args[@]}" python -m mypy
fi

if [[ "$SKIP_TESTS" -ne 1 ]]; then
  uv "${uv_run_args[@]}" python -m pytest
fi

if [[ "$SKIP_DOCKER" -ne 1 ]]; then
  docker_args=()
  if [[ "$FULL_RUNTIME" -eq 1 ]]; then
    docker_args+=(--full-runtime)
  fi

  if [[ "$BUILD_IMAGE" -eq 1 || "$FULL_RUNTIME" -eq 1 ]]; then
    "$ROOT_DIR/scripts/docker-preflight.sh" "${docker_args[@]}"
  else
    "$ROOT_DIR/scripts/docker-preflight.sh" --dry-run "${docker_args[@]}"
  fi
fi

if [[ "$SKIP_SECURITY" -ne 1 ]]; then
  "$ROOT_DIR/scripts/security-gate.sh"
fi

if [[ "$HOOK_MODE" -eq 1 ]]; then
  printf '%s\n' "Light hook mode completed. Real DOCKER_PREFLIGHT remains explicit via ./scripts/docker-preflight.sh before practical feature execution."
fi

printf '%s\n' "Repository operational checks completed."
