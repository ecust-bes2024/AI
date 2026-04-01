#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DEFAULT="/Users/jerry_hu/AI/sandbox/docs/team-c-codex-smoke"
BASE_DIR="${1:-$BASE_DEFAULT}"
STAMP="$(date +%s)"
TEAM_NAME="smoke-team-${STAMP}"
TEAM_DIR="${BASE_DIR}/${TEAM_NAME}"
TMP_REPO="${BASE_DIR}/repo-${STAMP}"
WORKTREE_PARENT="${BASE_DIR}/.worktrees-codex"

mkdir -p "${BASE_DIR}"

echo "Starting team-c smoke test"
echo "base: ${BASE_DIR}"
echo "team: ${TEAM_NAME}"

mkdir -p "${TMP_REPO}"
git -C "${TMP_REPO}" init -q
git -C "${TMP_REPO}" config user.name "team-c-smoke"
git -C "${TMP_REPO}" config user.email "team-c-smoke@example.com"
cat > "${TMP_REPO}/README.md" <<'EOF'
# team-c smoke repo
EOF
git -C "${TMP_REPO}" add README.md
git -C "${TMP_REPO}" commit -q -m "init smoke repo"

python3 "${SCRIPT_DIR}/team_runtime.py" --base "${BASE_DIR}" init "${TEAM_NAME}" \
  --lead lead \
  --mode in-process \
  --repo "${TMP_REPO}" \
  --teammate architect:architect::true \
  --teammate reviewer \
  --teammate qa \
  --require-plan-approval \
  --leader-plan-approval auto >/dev/null

cat > "${TEAM_DIR}/sample-plan.md" <<'EOF'
# Smoke Plan

- inspect ownership
- keep tests in scope
EOF

TASK1="$("${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-add "${TEAM_NAME}" "Review auth flow" --owner reviewer --deliverable reviewer.md --require-plan)"
TASK2="$("${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-add "${TEAM_NAME}" "Assess architecture" --owner architect --deliverable architect.md)"
TASK3="$("${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-add "${TEAM_NAME}" "Unassigned follow-up" --deliverable followup.md)"

"${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-update "${TEAM_NAME}" "${TASK2}" --owner qa >/dev/null

CLAIMED="$("${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-claim-next "${TEAM_NAME}" qa)"
if [[ "${CLAIMED}" != "${TASK3}" ]]; then
  echo "FAIL task-claim-next returned ${CLAIMED}, expected ${TASK3}"
  exit 1
fi

"${SCRIPT_DIR}/mailbox.sh" --base "${BASE_DIR}" mail-send "${TEAM_NAME}" \
  --sender reviewer \
  --recipient architect \
  --subject "Need boundary detail" \
  --body "Clarify token rotation ownership." >/dev/null

"${SCRIPT_DIR}/mailbox.sh" --base "${BASE_DIR}" ask-lead "${TEAM_NAME}" \
  --sender reviewer \
  --subject "Need approval" \
  --body "Can I widen the review scope for ${TASK1}?" >/dev/null

POP_JSON="$("${SCRIPT_DIR}/mailbox.sh" --base "${BASE_DIR}" mail-pop "${TEAM_NAME}" --recipient lead)"
ACK_TOKEN="$(printf '%s' "${POP_JSON}" | python3 -c 'import json,sys; payload=sys.stdin.read(); data=json.loads(payload) if payload.strip() else {}; messages=data.get("messages", []); print(messages[0]["ack_token"] if messages else "")')"

if [[ -z "${ACK_TOKEN}" ]]; then
  echo "FAIL mail-pop did not return an ack token for lead"
  exit 1
fi

"${SCRIPT_DIR}/mailbox.sh" --base "${BASE_DIR}" mail-ack "${TEAM_NAME}" "${ACK_TOKEN}" >/dev/null
"${SCRIPT_DIR}/mailbox.sh" --base "${BASE_DIR}" lead-triage "${TEAM_NAME}" --task-id "${TASK1}" >/dev/null

"${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" plan-request "${TEAM_NAME}" "${TASK1}" "${TEAM_DIR}/sample-plan.md" --note "Ready for review" >/dev/null

PLAN_STATUS="$(python3 - <<PY
import json
from pathlib import Path
board = json.loads(Path("${TEAM_DIR}/task-board.json").read_text())
task = next(task for task in board["tasks"] if task["task_id"] == "${TASK1}")
print(task["plan_status"])
PY
)"

if [[ "${PLAN_STATUS}" != "approved" ]]; then
  echo "FAIL auto-approved plan status was ${PLAN_STATUS}, expected approved"
  exit 1
fi

PLAN_RESPONSES="$(python3 - <<PY
import json
from pathlib import Path
lines = [json.loads(line) for line in Path("${TEAM_DIR}/mailbox.jsonl").read_text().splitlines() if line.strip()]
count = sum(1 for line in lines if line.get("kind") == "plan_approval_response")
print(count)
PY
)"

if [[ "${PLAN_RESPONSES}" -lt 1 ]]; then
  echo "FAIL expected at least one plan_approval_response mailbox entry"
  exit 1
fi

python3 - <<PY
import json
from pathlib import Path
team_dir = Path("${TEAM_DIR}")
board = json.loads((team_dir / "task-board.json").read_text())
lines = [json.loads(line) for line in Path("${TEAM_DIR}/mailbox.jsonl").read_text().splitlines() if line.strip()]
assert any(line.get("kind") == "task_assignment" and line.get("recipient") == "qa" for line in lines), lines
asks = [line for line in lines if line.get("kind") == "ask_lead"]
assert asks, lines
assert all(line.get("status") == "resolved" for line in asks), asks
assert any(line.get("kind") == "lead_triage" and line.get("recipient") == "reviewer" for line in lines), lines
assert any(line.get("kind") == "lead_broadcast" and line.get("recipient") == "qa" for line in lines), lines
task = next(task for task in board["tasks"] if task["task_id"] == "${TASK1}")
assert "[lead-triage" in task.get("notes", ""), task
print("mailbox extensions ok")
PY

"${SCRIPT_DIR}/lifecycle.sh" --base "${BASE_DIR}" heartbeat "${TEAM_NAME}" reviewer --note "Smoke review started" >/dev/null

if "${SCRIPT_DIR}/lifecycle.sh" --base "${BASE_DIR}" cleanup "${TEAM_NAME}" >/dev/null 2>&1; then
  echo "FAIL cleanup unexpectedly succeeded while teammates were active"
  exit 1
else
echo "OK   cleanup correctly blocked while teammates were active"
fi

"${SCRIPT_DIR}/lifecycle.sh" --base "${BASE_DIR}" set-state "${TEAM_NAME}" architect stopped >/dev/null
"${SCRIPT_DIR}/lifecycle.sh" --base "${BASE_DIR}" set-state "${TEAM_NAME}" reviewer completed >/dev/null
"${SCRIPT_DIR}/lifecycle.sh" --base "${BASE_DIR}" set-state "${TEAM_NAME}" qa shutdown >/dev/null
"${SCRIPT_DIR}/lifecycle.sh" --base "${BASE_DIR}" cleanup "${TEAM_NAME}" >/dev/null

for path in \
  "${TEAM_DIR}/team.json" \
  "${TEAM_DIR}/task-board.json" \
  "${TEAM_DIR}/task-board.md" \
  "${TEAM_DIR}/mailbox.jsonl" \
  "${TEAM_DIR}/mailbox.md" \
  "${TEAM_DIR}/lead-summary.md" \
  "${TEAM_DIR}/archive"; do
  if [[ ! -e "${path}" ]]; then
    echo "FAIL expected artifact missing: ${path}"
    exit 1
  fi
done

if find "${WORKTREE_PARENT}" -maxdepth 6 -type d -name architect | grep -q .; then
  echo "FAIL worktree directory still exists after cleanup"
  exit 1
fi

echo "OK   created tasks: ${TASK1}, ${TASK2}"
echo "OK   claim-next returned: ${CLAIMED}"
echo "OK   lead ack token: ${ACK_TOKEN}"
echo "OK   auto-approved plan status: ${PLAN_STATUS}"
echo "OK   assignment and ask-lead triage mailbox paths passed"
echo "OK   worktree lifecycle passed"
echo "OK   artifacts written under: ${TEAM_DIR}"
echo "Smoke test passed."
