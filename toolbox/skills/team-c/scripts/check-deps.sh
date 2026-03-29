#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
GLOBAL_SKILL_DIR="${HOME}/.codex/skills/team-c"

status=0

print_ok() {
  printf 'OK   %s\n' "$1"
}

print_warn() {
  printf 'WARN %s\n' "$1"
}

print_fail() {
  printf 'FAIL %s\n' "$1"
  status=1
}

printf 'team-c dependency check\n'
printf 'skill root: %s\n' "$SKILL_ROOT"
printf 'global skill target: %s\n' "$GLOBAL_SKILL_DIR"
printf '\n'

if command -v python3 >/dev/null 2>&1; then
  print_ok "python3 found at $(command -v python3)"
else
  print_fail "python3 not found"
fi

if command -v git >/dev/null 2>&1; then
  print_ok "git found at $(command -v git)"
else
  print_fail "git not found"
fi

if command -v tmux >/dev/null 2>&1; then
  print_ok "tmux found at $(command -v tmux)"
else
  print_warn "tmux not found; split-pane display will be unavailable"
fi

if [[ -f "${SKILL_ROOT}/SKILL.md" ]]; then
  print_ok "SKILL.md present"
else
  print_fail "SKILL.md missing"
fi

if [[ -f "${SCRIPT_DIR}/team_runtime.py" && -f "${SCRIPT_DIR}/display.py" ]]; then
  if python3 -m py_compile "${SCRIPT_DIR}/team_runtime.py" "${SCRIPT_DIR}/display.py" >/dev/null 2>&1; then
    print_ok "Python runtime scripts compile"
  else
    print_fail "Python runtime scripts failed to compile"
  fi
else
  print_fail "Runtime scripts missing"
fi

global_installed=0
if [[ -d "${GLOBAL_SKILL_DIR}" ]]; then
  global_installed=1
fi

if [[ -d "${HOME}/.codex/skills" ]]; then
  if [[ -w "${HOME}/.codex/skills" ]]; then
    print_ok "~/.codex/skills is writable"
  else
    if [[ "$global_installed" -eq 1 ]]; then
      print_warn "~/.codex/skills is not writable in the current environment, but team-c is already installed globally"
    else
      print_fail "~/.codex/skills exists but is not writable"
    fi
  fi
else
  parent_dir="${HOME}/.codex"
  if [[ -d "${parent_dir}" && -w "${parent_dir}" ]]; then
    print_ok "~/.codex is writable; skill install can create ~/.codex/skills"
  else
    if [[ "$global_installed" -eq 1 ]]; then
      print_warn "~/.codex is not writable in the current environment, but team-c is already installed globally"
    else
      print_fail "~/.codex is not writable; global install may fail"
    fi
  fi
fi

if [[ "$global_installed" -eq 1 ]]; then
  print_ok "team-c appears installed globally"
else
  print_warn "team-c is not currently installed globally"
fi

printf '\n'
if [[ "$status" -eq 0 ]]; then
  printf 'Dependency check passed.\n'
else
  printf 'Dependency check failed.\n'
fi

exit "$status"
