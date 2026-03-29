#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPATCH="${SCRIPT_DIR}/lab-dispatch.sh"

if [[ $# -eq 0 ]]; then
  echo "Usage: guarded-shell.sh <command...>" >&2
  exit 1
fi

cmd="$*"
cwd="$(pwd)"

pre_payload=$(python3 - <<'PY' "$cmd" "$cwd"
import json, sys
cmd = sys.argv[1]
cwd = sys.argv[2]
print(json.dumps({
    "hook_event_name": "PreToolUse",
    "tool_name": "shell",
    "tool_input": {"cmd": cmd},
    "cwd": cwd,
    "session_id": "hooks-codex-guarded-shell",
}))
PY
)

pre_result="$("${DISPATCH}" --event pre_tool_use --payload-json "${pre_payload}")" || {
  printf '%s\n' "${pre_result:-}"
  exit 2
}

updated_cmd="$(printf '%s' "${pre_result}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); upd=data.get("updatedInput") or {}; print(upd.get("cmd",""))')"
additional_context="$(printf '%s' "${pre_result}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); print(data.get("additionalContext",""))')"
if [[ -n "${updated_cmd}" ]]; then
  cmd="${updated_cmd}"
fi
if [[ -n "${additional_context}" ]]; then
  printf '[hooks-codex] %s\n' "${additional_context}" >&2
fi

if [[ "${cmd}" == *"rm -rf"* || "${cmd}" == *"git push --force"* || "${cmd}" == *"git clean -fd"* ]]; then
  perm_payload=$(python3 - <<'PY' "$cmd" "$cwd"
import json, sys
cmd = sys.argv[1]
cwd = sys.argv[2]
print(json.dumps({
    "hook_event_name": "PermissionRequest",
    "tool_name": "shell",
    "tool_input": {"cmd": cmd},
    "permission_suggestions": ["allow", "ask"],
    "cwd": cwd,
    "session_id": "hooks-codex-guarded-shell",
}))
PY
)

  perm_result="$("${DISPATCH}" --event permission_request --payload-json "${perm_payload}")" || {
    printf '%s\n' "${perm_result:-}"
    exit 2
  }
fi

exec /bin/zsh -lc "${cmd}"
