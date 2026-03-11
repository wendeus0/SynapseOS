#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="container_aggressive"
SERVICE="codex-dev"
START_RUNTIME=0
BUILD=0

export DOCKER_CONFIG="${DOCKER_CONFIG:-$ROOT_DIR/.cache/docker/config}"
export AIGNT_DEV_UID="${AIGNT_DEV_UID:-$(id -u)}"
export AIGNT_DEV_GID="${AIGNT_DEV_GID:-$(id -g)}"
export AIGNT_OS_UID="${AIGNT_OS_UID:-$(id -u)}"
export AIGNT_OS_GID="${AIGNT_OS_GID:-$(id -g)}"

mkdir -p "$DOCKER_CONFIG"

usage() {
  cat <<'EOF'
Usage: ./scripts/dev-codex.sh [--build] [--with-runtime] [--profile <name>] [-- <codex-args...>]

Starts the isolated Codex development container with:
  docker compose -f compose.yaml -f compose.dev.yaml ...

Options:
  --build          Force image rebuild before starting the container.
  --with-runtime   Also start the runtime service from compose.yaml.
  --profile NAME   Codex profile from .codex/config.toml. Default: container_aggressive
  --help           Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)
      BUILD=1
      shift
      ;;
    --with-runtime)
      START_RUNTIME=1
      shift
      ;;
    --profile)
      PROFILE="${2:?missing value for --profile}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

compose_cmd=(docker compose -f "$ROOT_DIR/compose.yaml" -f "$ROOT_DIR/compose.dev.yaml")
up_cmd=("${compose_cmd[@]}" up --detach)

if [[ "$BUILD" -eq 1 ]]; then
  up_cmd+=(--build)
fi

if [[ "$START_RUNTIME" -eq 1 ]]; then
  up_cmd+=(aignt-os "$SERVICE")
else
  up_cmd+=("$SERVICE")
fi

printf '%s\n' "Resolved dev environment command: ${up_cmd[*]}"
"${up_cmd[@]}"

exec_cmd=(
  "${compose_cmd[@]}"
  exec
  -e "CODEX_PROFILE=$PROFILE"
  "$SERVICE"
  bash
  -lc
  'set -euo pipefail
mkdir -p "$HOME/.codex"
if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" && -n "${GITHUB_TOKEN:-}" ]]; then
  export GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
fi
rm -f "$HOME/.codex/config.toml"
cp /workspace/.codex/config.toml "$HOME/.codex/config.toml"
if [[ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  cat >>"$HOME/.codex/config.toml" <<'"'"'EOF'"'"'

[mcp_servers.github]
command = "github-mcp-server"
args = ["--toolsets=default,actions", "stdio"]
EOF
else
  printf "%s\n" "Codex MCP note: GitHub MCP desabilitado; defina GITHUB_PERSONAL_ACCESS_TOKEN para habilitar GitHub e GitHub Actions." >&2
fi
exec codex -p "$CODEX_PROFILE" "$@"'
  bash
)

if [[ $# -gt 0 ]]; then
  exec_cmd+=("$@")
fi

printf '%s\n' "Resolved Codex command: codex -p $PROFILE${*:+ $*}"
"${exec_cmd[@]}"
