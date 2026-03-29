#!/usr/bin/env bash
set -euo pipefail

SRC_ROOT="/Users/jerry_hu/AI/toolbox/skills/team-c"
DEST_ROOT="${HOME}/.codex/skills"

mkdir -p "${DEST_ROOT}"
rm -rf "${DEST_ROOT}/team-c"
cp -R "${SRC_ROOT}" "${DEST_ROOT}/team-c"

echo "Installed:"
echo "- ${DEST_ROOT}/team-c"
