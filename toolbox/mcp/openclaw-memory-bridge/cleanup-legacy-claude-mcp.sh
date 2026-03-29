#!/usr/bin/env bash
set -euo pipefail

TARGET="${HOME}/.claude/.mcp.json"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${HOME}/.claude/backups"
WORKSPACE_BACKUP_DIR="/Users/jerry_hu/AI/sandbox/claude-mcp-cleanup"
DISABLED_PATH="${HOME}/.claude/.mcp.json.disabled-${STAMP}"
HOME_BACKUP_PATH="${BACKUP_DIR}/.mcp.json.backup-${STAMP}"
WORKSPACE_BACKUP_PATH="${WORKSPACE_BACKUP_DIR}/.mcp.json.backup-${STAMP}"

if [[ ! -f "$TARGET" ]]; then
  echo "No legacy file found at ${TARGET}"
  exit 0
fi

mkdir -p "$BACKUP_DIR"
mkdir -p "$WORKSPACE_BACKUP_DIR"

cp "$TARGET" "$HOME_BACKUP_PATH"
cp "$TARGET" "$WORKSPACE_BACKUP_PATH"
mv "$TARGET" "$DISABLED_PATH"

echo "Disabled legacy Claude MCP config."
echo "Original: $TARGET"
echo "Disabled copy: $DISABLED_PATH"
echo "Home backup: $HOME_BACKUP_PATH"
echo "Workspace backup: $WORKSPACE_BACKUP_PATH"
