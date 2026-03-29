#!/usr/bin/env bash
set -euo pipefail

LABEL="${OPENCLAW_MEMORY_LAUNCHD_LABEL:-com.jerryhu.openclaw-memory-http}"
HOST="${OPENCLAW_MEMORY_SERVER_HOST:-127.0.0.1}"
PORT="${OPENCLAW_MEMORY_SERVER_PORT:-4312}"
TOKEN="${OPENCLAW_MEMORY_SERVER_TOKEN:-}"
OPENCLAW_BRIDGE_TIMEOUT_MS="${OPENCLAW_BRIDGE_TIMEOUT_MS:-15000}"
OPENCLAW_MEMORY_SERVER_TIMEOUT_MS="${OPENCLAW_MEMORY_SERVER_TIMEOUT_MS:-20000}"
NODE_BIN="${NODE_BIN:-$(command -v node || true)}"
OPENCLAW_BIN="${OPENCLAW_BIN:-$(command -v openclaw || true)}"
DRY_RUN=0
NO_LOAD=0
PLIST_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-load)
      NO_LOAD=1
      shift
      ;;
    --plist-path)
      PLIST_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$NODE_BIN" || ! -x "$NODE_BIN" ]]; then
  echo "Unable to find a usable node binary. Set NODE_BIN explicitly." >&2
  exit 1
fi

if [[ -z "$OPENCLAW_BIN" || ! -x "$OPENCLAW_BIN" ]]; then
  echo "Unable to find a usable openclaw binary. Set OPENCLAW_BIN explicitly." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/memory-http-server.mjs"
UID_VALUE="$(id -u)"
LOG_DIR="${OPENCLAW_MEMORY_LOG_DIR:-${HOME}/Library/Logs/openclaw-memory-bridge}"
DEFAULT_PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
PLIST_PATH="${PLIST_PATH:-$DEFAULT_PLIST_PATH}"
LAUNCHD_PATH="$(dirname "$NODE_BIN"):$(dirname "$OPENCLAW_BIN"):/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "$(dirname "$PLIST_PATH")"

if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$LOG_DIR"
fi

cat >"$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${NODE_BIN}</string>
    <string>${SERVER_SCRIPT}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${SCRIPT_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>OPENCLAW_MEMORY_SERVER_HOST</key>
    <string>${HOST}</string>
    <key>OPENCLAW_MEMORY_SERVER_PORT</key>
    <string>${PORT}</string>
    <key>OPENCLAW_BIN</key>
    <string>${OPENCLAW_BIN}</string>
    <key>OPENCLAW_BRIDGE_TIMEOUT_MS</key>
    <string>${OPENCLAW_BRIDGE_TIMEOUT_MS}</string>
    <key>OPENCLAW_MEMORY_SERVER_TIMEOUT_MS</key>
    <string>${OPENCLAW_MEMORY_SERVER_TIMEOUT_MS}</string>
    <key>PATH</key>
    <string>${LAUNCHD_PATH}</string>
PLIST

if [[ -n "$TOKEN" ]]; then
  cat >>"$PLIST_PATH" <<PLIST
    <key>OPENCLAW_MEMORY_SERVER_TOKEN</key>
    <string>${TOKEN}</string>
PLIST
fi

cat >>"$PLIST_PATH" <<PLIST
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/${LABEL}.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/${LABEL}.error.log</string>
</dict>
</plist>
PLIST

echo "Wrote plist: $PLIST_PATH"

if [[ "$DRY_RUN" -eq 1 ]]; then
  cat "$PLIST_PATH"
  exit 0
fi

if [[ "$NO_LOAD" -eq 1 ]]; then
  echo "Skipped launchctl bootstrap because --no-load was provided."
  exit 0
fi

launchctl bootout "gui/${UID_VALUE}" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/${UID_VALUE}" "$PLIST_PATH"
launchctl kickstart -k "gui/${UID_VALUE}/${LABEL}"

echo "Installed and started ${LABEL}"
echo "Health check: curl http://${HOST}:${PORT}/health"
echo "Logs: ${LOG_DIR}/${LABEL}.log"
