#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="aignt-os"
SKIP_UP=1
DRY_RUN=0
HEALTH_TIMEOUT=30
BUILD_MODE="config-only"
BUILD_MODE_EXPLICIT=0

export DOCKER_CONFIG="${DOCKER_CONFIG:-$ROOT_DIR/.cache/docker/config}"
mkdir -p "$DOCKER_CONFIG"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      SERVICE="${2:?missing value for --service}"
      shift 2
      ;;
    --skip-build)
      BUILD_MODE="config-only"
      BUILD_MODE_EXPLICIT=1
      shift
      ;;
    --build)
      BUILD_MODE="always"
      BUILD_MODE_EXPLICIT=1
      shift
      ;;
    --build-if-needed)
      BUILD_MODE="if-needed"
      BUILD_MODE_EXPLICIT=1
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
    --health-timeout)
      HEALTH_TIMEOUT="${2:?missing value for --health-timeout}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

config_cmd=(docker compose -f "$ROOT_DIR/compose.yaml" config)
build_cmd=("$ROOT_DIR/scripts/docker-build.sh" --use-compose)
rebuild_cmd=("$ROOT_DIR/scripts/docker-rebuild.sh" --use-compose)
up_cmd=("$ROOT_DIR/scripts/docker-up.sh" --service "$SERVICE" --detach)

if [[ "$SKIP_UP" -ne 1 && "$BUILD_MODE_EXPLICIT" -ne 1 ]]; then
  BUILD_MODE="if-needed"
fi

printf '%s\n' "Resolved preflight config command: ${config_cmd[*]}"
if [[ "$BUILD_MODE" == "always" ]]; then
  printf '%s\n' "Resolved preflight build command: ${build_cmd[*]}"
elif [[ "$BUILD_MODE" == "if-needed" ]]; then
  printf '%s\n' "Resolved preflight rebuild command: ${rebuild_cmd[*]}"
else
  printf '%s\n' "Resolved preflight build mode: config-only"
fi
if [[ "$SKIP_UP" -ne 1 ]]; then
  printf '%s\n' "Resolved preflight up command: ${up_cmd[*]}"
  printf '%s\n' "Resolved preflight health requirement: container must stay running and report healthy"
else
  printf '%s\n' "Resolved preflight runtime mode: skip-up (default)"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  exit 0
fi

"${config_cmd[@]}"

if [[ "$BUILD_MODE" == "always" ]]; then
  "${build_cmd[@]}"
elif [[ "$BUILD_MODE" == "if-needed" ]]; then
  "${rebuild_cmd[@]}"
fi

if [[ "$SKIP_UP" -ne 1 ]]; then
  "${up_cmd[@]}"
  container_id="$(docker compose -f "$ROOT_DIR/compose.yaml" ps -q "$SERVICE")"
  if [[ -z "$container_id" ]]; then
    echo "Container for service '$SERVICE' was not created." >&2
    exit 1
  fi

  deadline=$((SECONDS + HEALTH_TIMEOUT))
  while (( SECONDS < deadline )); do
    status="$(docker inspect --format '{{.State.Status}}' "$container_id")"
    health_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container_id")"

    if [[ "$status" != "running" ]]; then
      echo "Container for service '$SERVICE' is not running (status=$status)." >&2
      exit 1
    fi

    if [[ "$health_status" == "no-healthcheck" ]]; then
      echo "Container for service '$SERVICE' does not declare a healthcheck." >&2
      exit 1
    fi

    if [[ "$health_status" == "healthy" ]]; then
      printf '%s\n' "Container '$SERVICE' status: $status health: $health_status"
      break
    fi

    sleep 1
  done

  final_status="$(docker inspect --format '{{.State.Status}}' "$container_id")"
  final_health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container_id")"
  if [[ "$final_status" != "running" ]]; then
    echo "Container for service '$SERVICE' did not remain running (status=$final_status)." >&2
    exit 1
  fi
  if [[ "$final_health" == "no-healthcheck" ]]; then
    echo "Container for service '$SERVICE' does not declare a healthcheck." >&2
    exit 1
  fi
  if [[ "$final_health" != "healthy" ]]; then
    echo "Container for service '$SERVICE' did not reach healthy state (health=$final_health)." >&2
    exit 1
  fi
fi

printf '%s\n' "Docker preflight passed."
