#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

git -C "$ROOT_DIR" config core.hooksPath .githooks
chmod +x "$ROOT_DIR"/scripts/*.sh
chmod +x "$ROOT_DIR"/.githooks/*

printf '%s\n' "Git hooks installed via .githooks/."
