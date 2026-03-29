#!/usr/bin/env bash
set -euo pipefail

HOME_DIR="${HOME}"
RESULT_DIR="${HOME_DIR}/AI/tmp/codex-search-results"
CODEX_BIN="${CODEX_BIN:-/Users/jerry_hu/.nvm/versions/node/v24.12.0/bin/codex}"

PROMPT=""
OUTPUT=""
MODEL="gpt-5.4"
SANDBOX="workspace-write"
TIMEOUT=180
TASK_NAME="search-$(date +%s)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt) PROMPT="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --task-name) TASK_NAME="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "ERROR: --prompt is required"
  exit 1
fi

mkdir -p "$RESULT_DIR"

TASK_DIR="${RESULT_DIR}/${TASK_NAME}"
mkdir -p "$TASK_DIR"

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="${TASK_DIR}/report.md"
fi

META_FILE="${TASK_DIR}/meta.json"
LOG_FILE="${TASK_DIR}/task-output.txt"
LATEST_META_FILE="${RESULT_DIR}/latest-meta.json"
STARTED_AT="$(date -Iseconds)"

jq -n \
  --arg name "$TASK_NAME" \
  --arg prompt "$PROMPT" \
  --arg output "$OUTPUT" \
  --arg task_dir "$TASK_DIR" \
  --arg log_file "$LOG_FILE" \
  --arg ts "$STARTED_AT" \
  '{task_name: $name, prompt: $prompt, output: $output, task_dir: $task_dir, log_file: $log_file, started_at: $ts, status: "running"}' \
  | tee "$META_FILE" > "$LATEST_META_FILE"

cat > "$OUTPUT" <<EOF
# Deep Search Report
**Query:** $PROMPT
**Status:** In progress...
---
EOF

SEARCH_INSTRUCTION="You are a research assistant. Search the web for the following query.

CRITICAL RULES:
1. Write findings to $OUTPUT incrementally after each search round, overwriting or appending as needed so the file always contains the latest usable draft.
2. Keep searches focused, max 8 web searches.
3. Include source URLs inline for every key claim.
4. End with a brief summary section.
5. If time is nearly exhausted, write a partial but readable final draft to $OUTPUT before exiting.

Query: $PROMPT"

echo "[codex-deep-search] Task: $TASK_NAME"
echo "[codex-deep-search] Task dir: $TASK_DIR"
echo "[codex-deep-search] Output: $OUTPUT"
echo "[codex-deep-search] Log: $LOG_FILE"
echo "[codex-deep-search] Model: $MODEL | Timeout: ${TIMEOUT}s"

run_with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$TIMEOUT" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$TIMEOUT" "$@"
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$TIMEOUT" "$@" <<'PY'
import os
import signal
import subprocess
import sys

if len(sys.argv) < 3:
    print("usage: python timeout-wrapper.py <seconds> <cmd> [args...]", file=sys.stderr)
    sys.exit(2)

seconds = int(sys.argv[1])
cmd = sys.argv[2:]
proc = subprocess.Popen(cmd)
try:
    sys.exit(proc.wait(timeout=seconds))
except subprocess.TimeoutExpired:
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    sys.exit(124)
PY
  else
    echo "ERROR: no timeout implementation found (need timeout, gtimeout, or python3)" >&2
    return 127
  fi
}

run_with_timeout "$CODEX_BIN" exec \
  --model "$MODEL" \
  --full-auto \
  --sandbox "$SANDBOX" \
  --add-dir "$HOME_DIR/AI" \
  -c 'model_reasoning_effort="low"' \
  "$SEARCH_INSTRUCTION" 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [[ -f "$OUTPUT" ]]; then
  echo -e "\n---\n_Search completed at $(date -u)_" >> "$OUTPUT"
fi

LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo 0)
COMPLETED_AT="$(date -Iseconds)"
START_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$STARTED_AT" +%s 2>/dev/null || python3 - <<'PY'
from datetime import datetime
import os
print(int(datetime.fromisoformat(os.environ['STARTED_AT']).timestamp()))
PY
)
END_TS=$(date +%s)
ELAPSED=$(( END_TS - START_TS ))
MINS=$(( ELAPSED / 60 ))
SECS=$(( ELAPSED % 60 ))
DURATION="${MINS}m${SECS}s"

jq -n \
  --arg name "$TASK_NAME" \
  --arg prompt "$PROMPT" \
  --arg output "$OUTPUT" \
  --arg task_dir "$TASK_DIR" \
  --arg log_file "$LOG_FILE" \
  --arg started "$STARTED_AT" \
  --arg completed "$COMPLETED_AT" \
  --arg duration "$DURATION" \
  --arg lines "$LINES" \
  --argjson exit_code "$EXIT_CODE" \
  '{task_name: $name, prompt: $prompt, output: $output, task_dir: $task_dir, log_file: $log_file, started_at: $started, completed_at: $completed, duration: $duration, lines: ($lines|tonumber), exit_code: $exit_code, status: (if $exit_code == 0 then "done" elif $exit_code == 124 then "timeout" else "failed" end)}' \
  | tee "$META_FILE" > "$LATEST_META_FILE"

echo "[codex-deep-search] Done (${DURATION}, exit=${EXIT_CODE}, ${LINES} lines)"
