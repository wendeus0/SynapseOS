#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
failures=0

search_has_matches() {
  local pattern="$1"
  shift

  if command -v rg >/dev/null 2>&1; then
    rg -n "$pattern" "$@" >/dev/null 2>&1
    return
  fi

  grep -nE "$pattern" "$@" >/dev/null 2>&1
}

search_print_matches() {
  local pattern="$1"
  shift

  if command -v rg >/dev/null 2>&1; then
    rg -n "$pattern" "$@" >&2
    return
  fi

  grep -nE "$pattern" "$@" >&2
}

check_pattern() {
  local description="$1"
  local pattern="$2"
  shift 2

  if search_has_matches "$pattern" "$@"; then
    echo "Security gate failed: ${description}" >&2
    search_print_matches "$pattern" "$@"
    failures=1
  fi
}

mapfile -t workflow_files < <(find "$ROOT_DIR/.github/workflows" -maxdepth 1 -type f \( -name "*.yml" -o -name "*.yaml" \) | sort)
mapfile -t script_files < <(find "$ROOT_DIR/scripts" -maxdepth 1 -type f -name "*.sh" ! -name "security-gate.sh" | sort)

for workflow_file in "${workflow_files[@]}"; do
  if ! search_has_matches '^permissions:' "$workflow_file"; then
    echo "Security gate failed: workflow without explicit permissions: $workflow_file" >&2
    failures=1
  fi
done

if ((${#workflow_files[@]} > 0)); then
  check_pattern "workflow with write-all permissions" 'permissions:[[:space:]]*write-all' "${workflow_files[@]}"
fi

if ((${#script_files[@]} > 0)); then
  check_pattern "script with eval usage" '(^|[^[:alnum:]_])eval([^[:alnum:]_]|$)' "${script_files[@]}"
  check_pattern "script piping curl directly to shell" 'curl[[:space:]].*[|][[:space:]]*(sh|bash)([^[:alnum:]_]|$)' "${script_files[@]}"
  check_pattern "script piping wget directly to shell" 'wget[[:space:]].*[|][[:space:]]*(sh|bash)([^[:alnum:]_]|$)' "${script_files[@]}"
  check_pattern "script with chmod 777" 'chmod[[:space:]]+777([^[:alnum:]_]|$)' "${script_files[@]}"
fi

check_pattern "Docker or Compose using privileged mode" '(^|[[:space:]])--privileged([[:space:]]|$)|privileged:[[:space:]]*true' \
  "$ROOT_DIR/Dockerfile" "$ROOT_DIR/compose.yaml"
check_pattern "Docker or Compose mounting docker.sock" 'docker\.sock' \
  "$ROOT_DIR/Dockerfile" "$ROOT_DIR/compose.yaml"

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

printf '%s\n' "Security gate passed."
