#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="aignt-os"
SKIP_BUILD=0
SKIP_UP=1
DRY_RUN=0

export DOCKER_CONFIG="${DOCKER_CONFIG:-$ROOT_DIR/.cache/docker/config}"
mkdir -p "$DOCKER_CONFIG"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      SERVICE="${2:?missing value for --service}"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    --skip-up)
      SKIP_UP=1
      shift
      ;;
    --full-runtime)
      SKIP_UP=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

config_cmd=(docker compose -f "$ROOT_DIR/compose.yaml" config)
build_cmd=("$ROOT_DIR/scripts/docker-build.sh" --use-compose)
up_cmd=("$ROOT_DIR/scripts/docker-up.sh" --service "$SERVICE")

printf '%s\n' "Resolved preflight config command: ${config_cmd[*]}"
if [[ "$SKIP_BUILD" -ne 1 ]]; then
  printf '%s\n' "Resolved preflight build command: ${build_cmd[*]}"
fi
if [[ "$SKIP_UP" -ne 1 ]]; then
  printf '%s\n' "Resolved preflight up command: ${up_cmd[*]}"
else
  printf '%s\n' "Resolved preflight mode: light (--skip-up default)"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  exit 0
fi

"${config_cmd[@]}"

if [[ "$SKIP_BUILD" -ne 1 ]]; then
  "${build_cmd[@]}"
fi

if [[ "$SKIP_UP" -ne 1 ]]; then
  "${up_cmd[@]}"
fi

printf '%s\n' "Docker preflight passed."
