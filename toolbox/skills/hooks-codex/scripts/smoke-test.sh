#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="/Users/jerry_hu/AI/sandbox/docs/hooks-codex-smoke"
CONFIG_FILE="${TMP_DIR}/hooks.toml"
STAMP="$(date +%s)"
REPO_DIR="${TMP_DIR}/repo-${STAMP}"
WORKTREE_PATH="${TMP_DIR}/wt-worker-${STAMP}"
mkdir -p "${TMP_DIR}"

cat > "${CONFIG_FILE}" <<EOF
[hooks]

[[hooks.pre_tool_use]]
type = "command"
command = ["python3", "/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/pre_tool_use.py"]
timeout = 5

[hooks.pre_tool_use.matcher]
tool_name_regex = "^(shell|exec)$"

[[hooks.permission_request]]
type = "command"
command = ["python3", "/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/permission_request.py"]
timeout = 5

[hooks.permission_request.matcher]
tool_name_regex = "^(shell|exec)$"

[[hooks.task_completed]]
type = "command"
command = ["python3", "/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/task_completed.py"]
timeout = 5

[[hooks.lead_reply]]
type = "command"
command = ["python3", "/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/lead_reply.py"]
timeout = 5

[[hooks.worktree_create]]
type = "command"
command = ["python3", "/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/worktree_create.py"]
timeout = 20

[[hooks.worktree_remove]]
type = "command"
command = ["python3", "/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/worktree_remove.py"]
timeout = 20
EOF

mkdir -p "${REPO_DIR}"
git -C "${REPO_DIR}" init -q
git -C "${REPO_DIR}" config user.name "hooks-codex-smoke"
git -C "${REPO_DIR}" config user.email "hooks-codex-smoke@example.com"
cat > "${REPO_DIR}/README.md" <<'EOF'
# hooks-codex smoke repo
EOF
git -C "${REPO_DIR}" add README.md
git -C "${REPO_DIR}" commit -q -m "init smoke repo"

ALLOW_JSON="$("${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event pre_tool_use --payload-json '{"hook_event_name":"PreToolUse","tool_name":"shell","tool_input":{"cmd":"pytest tests/auth -q"},"cwd":"/tmp","session_id":"smoke"}')"
DENY_FILE="${TMP_DIR}/deny.json"
if "${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event pre_tool_use --payload-json '{"hook_event_name":"PreToolUse","tool_name":"shell","tool_input":{"cmd":"rm -rf /"},"cwd":"/tmp","session_id":"smoke"}' > "${DENY_FILE}" 2>/dev/null; then
  echo "FAIL destructive pre_tool_use was not blocked"
  exit 1
fi

PERM_ALLOW_JSON="$("${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event permission_request --payload-json '{"hook_event_name":"PermissionRequest","tool_name":"shell","tool_input":{"cmd":"git status"},"permission_suggestions":["allow","ask"],"cwd":"/tmp","session_id":"smoke"}')"
PERM_ASK_FILE="${TMP_DIR}/permission-ask.json"
if "${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event permission_request --payload-json '{"hook_event_name":"PermissionRequest","tool_name":"shell","tool_input":{"cmd":"git push --force"},"permission_suggestions":["allow","ask"],"cwd":"/tmp","session_id":"smoke"}' > "${PERM_ASK_FILE}" 2>/dev/null; then
  echo "FAIL permission_request ask path did not block"
  exit 1
fi

TASK_JSON="$("${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event task_completed --payload-json '{"hook_event_name":"TaskCompleted","task_id":"T1","task_subject":"Implement auth retry","team_name":"demo","teammate_name":"worker"}')"
REPLY_JSON="$("${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event lead_reply --payload-json '{"hook_event_name":"LeadReply","team_name":"demo","sender":"lead","recipient":"worker","subject":"Scope approved","body":"Include retry logic."}')"
WORKTREE_JSON="$("${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event worktree_create --payload-json "{\"hook_event_name\":\"WorktreeCreate\",\"name\":\"worker\",\"team_name\":\"demo\",\"teammate_name\":\"worker\",\"repo_root\":\"${REPO_DIR}\",\"requested_path\":\"${WORKTREE_PATH}\",\"branch_name\":\"demo-worker-${STAMP}-codex\"}")"

printf '%s' "${ALLOW_JSON}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); assert data["ok"] is True; assert data["decision"] == "allow"'
printf '%s' "${PERM_ALLOW_JSON}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); assert data["ok"] is True; assert data["decision"] == "allow"'

python3 - "${DENY_FILE}" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data["ok"] is False
assert data["decision"] in {"deny", "block"}
PY

python3 - "${PERM_ASK_FILE}" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data["ok"] is False
assert data["decision"] in {"ask", "deny", "block"}
PY

printf '%s' "${TASK_JSON}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); assert data["ok"] is True; assert "additionalContext" in data'
printf '%s' "${REPLY_JSON}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); assert data["ok"] is True; assert "additionalContext" in data'
printf '%s' "${WORKTREE_JSON}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); assert data["ok"] is True; assert "wt-worker-" in data["worktreePath"]'

"${SCRIPT_DIR}/dispatch-hook.sh" --config "${CONFIG_FILE}" --event worktree_remove --payload-json "{\"hook_event_name\":\"WorktreeRemove\",\"worktree_path\":\"${WORKTREE_PATH}\",\"repo_root\":\"${REPO_DIR}\",\"force\":false}" >/dev/null

if [[ -d "${WORKTREE_PATH}" ]]; then
  echo "FAIL worktree_remove did not remove the worktree directory"
  exit 1
fi

echo "OK   pre_tool_use allow path passed"
echo "OK   pre_tool_use deny path passed"
echo "OK   permission_request allow path passed"
echo "OK   permission_request ask path passed"
echo "OK   task_completed context injection passed"
echo "OK   lead_reply context injection passed"
echo "OK   worktree_create / worktree_remove passed"
echo "Smoke test passed."
