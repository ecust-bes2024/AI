# Runtime Feature Map

This file maps Claude `agent teams` semantics to the current `team-c` runtime.

| Claude concept | Team-C runtime |
|---|---|
| shared task list | `docs/research/team-c-codex/<team>/task-board.json` + `task-board.md` |
| teammate direct messaging | `docs/research/team-c-codex/<team>/mailbox.jsonl` + `mailbox.md` |
| lead/teammate lifecycle | `docs/research/team-c-codex/<team>/team.json` teammate states + lifecycle commands |
| plan approval | `plan-request`, `plan-approve`, `plan-reject` |
| cleanup semantics | `cleanup` command, blocked while teammates are active |
| in-process display | `display.py watch` dashboard |
| split panes | `start-split-panes.sh` using tmux |

## Important limitation

This runtime gives you protocol and artifact semantics, not a native Claude transport.

What is implemented:

- explicit state
- explicit coordination artifacts
- explicit cleanup checks
- explicit mailbox entries
- explicit plan states
- explicit dashboard rendering

What is still emulated rather than native:

- automatic teammate transport
- native UI pane ownership
- native direct peer sockets
- native task-claim race handling across separate long-lived processes

Those gaps are acceptable for a workspace-backed orchestration layer, but they are not identical to Claude's built-in runtime.
