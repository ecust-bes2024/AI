#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(cd "${SCRIPT_DIR}/../templates" && pwd)"

status=0

say_ok() { printf 'OK   %s\n' "$1"; }
say_warn() { printf 'WARN %s\n' "$1"; }
say_fail() { printf 'FAIL %s\n' "$1"; status=1; }

printf 'hooks-codex dependency check\n'

if command -v python3 >/dev/null 2>&1; then
  say_ok "python3 found at $(command -v python3)"
else
  say_fail "python3 not found"
fi

for path in \
  "${TEMPLATE_DIR}/pre_tool_use.py" \
  "${TEMPLATE_DIR}/permission_request.py" \
  "${TEMPLATE_DIR}/task_completed.py" \
  "${TEMPLATE_DIR}/lead_reply.py" \
  "${TEMPLATE_DIR}/worktree_create.py" \
  "${TEMPLATE_DIR}/worktree_remove.py"; do
  if [[ -f "${path}" ]]; then
    say_ok "template present: ${path##*/}"
  else
    say_fail "missing template: ${path##*/}"
  fi
done

if python3 -m py_compile "${TEMPLATE_DIR}/pre_tool_use.py" "${TEMPLATE_DIR}/permission_request.py" "${TEMPLATE_DIR}/task_completed.py" "${TEMPLATE_DIR}/lead_reply.py" "${TEMPLATE_DIR}/worktree_create.py" "${TEMPLATE_DIR}/worktree_remove.py" >/dev/null 2>&1; then
  say_ok "template scripts compile"
else
  say_fail "template scripts failed to compile"
fi

printf '\n'
if [[ "$status" -eq 0 ]]; then
  printf 'Dependency check passed.\n'
else
  printf 'Dependency check failed.\n'
fi

exit "$status"
