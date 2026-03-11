#!/usr/bin/env bash
set -euo pipefail

SOURCE_CONFIG=""
OUTPUT_CONFIG=""

usage() {
  cat <<'EOF'
Usage: ./scripts/render-codex-config.sh --source <config.toml> --output <config.toml>

Renders the effective Codex config for the isolated development container.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE_CONFIG="${2:?missing value for --source}"
      shift 2
      ;;
    --output)
      OUTPUT_CONFIG="${2:?missing value for --output}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf '%s\n' "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$SOURCE_CONFIG" || -z "$OUTPUT_CONFIG" ]]; then
  usage >&2
  exit 1
fi

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" && -n "${GITHUB_TOKEN:-}" ]]; then
  export GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN"
fi

mkdir -p "$(dirname "$OUTPUT_CONFIG")"
rm -f "$OUTPUT_CONFIG"
cp "$SOURCE_CONFIG" "$OUTPUT_CONFIG"

if [[ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  cat >>"$OUTPUT_CONFIG" <<'EOF'

[mcp_servers.github]
command = "github-mcp-server"
args = ["--toolsets=default,actions", "stdio"]
EOF
else
  printf '%s\n' "Codex MCP note: GitHub MCP desabilitado; defina GITHUB_PERSONAL_ACCESS_TOKEN para habilitar GitHub e GitHub Actions." >&2
fi
