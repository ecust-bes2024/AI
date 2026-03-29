#!/usr/bin/env bash
set -euo pipefail

LABEL="${OPENCLAW_MEMORY_LAUNCHD_LABEL:-com.jerryhu.openclaw-memory-http}"
HOST="${OPENCLAW_MEMORY_SERVER_HOST:-127.0.0.1}"
PORT="${OPENCLAW_MEMORY_SERVER_PORT:-4312}"
UID_VALUE="$(id -u)"

echo "launchctl status for ${LABEL}:"
launchctl print "gui/${UID_VALUE}/${LABEL}" 2>/dev/null || echo "Service not loaded."
echo
echo "HTTP health:"
curl -fsS "http://${HOST}:${PORT}/health" || echo "Health endpoint unavailable."
