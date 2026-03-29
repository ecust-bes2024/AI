#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/../config/hooks-codex.lab.toml"

exec python3 "${SCRIPT_DIR}/hooks_runtime.py" dispatch --config "${CONFIG}" "$@"
