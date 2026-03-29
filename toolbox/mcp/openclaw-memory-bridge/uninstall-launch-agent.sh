#!/usr/bin/env bash
set -euo pipefail

LABEL="${OPENCLAW_MEMORY_LAUNCHD_LABEL:-com.jerryhu.openclaw-memory-http}"
UID_VALUE="$(id -u)"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
KEEP_PLIST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-plist)
      KEEP_PLIST=1
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

launchctl bootout "gui/${UID_VALUE}" "$PLIST_PATH" >/dev/null 2>&1 || true

if [[ "$KEEP_PLIST" -eq 0 && -f "$PLIST_PATH" ]]; then
  rm -f "$PLIST_PATH"
  echo "Removed plist: $PLIST_PATH"
fi

echo "Stopped ${LABEL}"
