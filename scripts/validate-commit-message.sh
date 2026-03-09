#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <commit-message-file>" >&2
  exit 1
fi

message_file="$1"
message="$(grep -vE '^(#|$)' "$message_file" | head -n 1 || true)"
pattern='^(build|chore|ci|docs|feat|fix|perf|refactor|revert|test)(\([a-z0-9._/-]+\))?!?: .{1,72}$'

if [[ -z "$message" ]]; then
  echo "Commit message is empty." >&2
  exit 1
fi

if [[ "$message" =~ $pattern ]]; then
  printf '%s\n' "Commit message validated: $message"
  exit 0
fi

echo "Commit message must follow conventional commit format." >&2
exit 1
