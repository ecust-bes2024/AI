#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DEFAULT="/Users/jerry_hu/AI/sandbox/docs/team-c-codex-smoke"
BASE_DIR="${1:-$BASE_DEFAULT}"
STAMP="$(date +%s)"
TEAM_NAME="smoke-team-${STAMP}"
TEAM_DIR="${BASE_DIR}/${TEAM_NAME}"

mkdir -p "${BASE_DIR}"

echo "Starting team-c smoke test"
echo "base: ${BASE_DIR}"
echo "team: ${TEAM_NAME}"

python3 "${SCRIPT_DIR}/team_runtime.py" --base "${BASE_DIR}" init "${TEAM_NAME}" \
  --lead lead \
  --mode in-process \
  --teammate architect \
  --teammate reviewer \
  --teammate qa \
  --require-plan-approval >/dev/null

cat > "${TEAM_DIR}/sample-plan.md" <<'EOF'
# Smoke Plan

- inspect ownership
- keep tests in scope
EOF

TASK1="$("${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-add "${TEAM_NAME}" "Review auth flow" --owner reviewer --deliverable reviewer.md --require-plan)"
TASK2="$("${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" task-add "${TEAM_NAME}" "Assess architecture" --owner architect --deliverable architect.md)"

"${SCRIPT_DIR}/mailbox.sh" --base "${BASE_DIR}" mail-send "${TEAM_NAME}" \
  --sender reviewer \
  --recipient architect \
  --subject "Need boundary detail" \
  --body "Clarify token rotation ownership." >/dev/null

"${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" plan-request "${TEAM_NAME}" "${TASK1}" "${TEAM_DIR}/sample-plan.md" --note "Ready for review" >/dev/null
"${SCRIPT_DIR}/task-board.sh" --base "${BASE_DIR}" plan-approve "${TEAM_NAME}" "${TASK1}" --note "Approved" >/dev/null
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

echo "OK   created tasks: ${TASK1}, ${TASK2}"
echo "OK   artifacts written under: ${TEAM_DIR}"
echo "Smoke test passed."
