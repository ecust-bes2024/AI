# Runtime Feature Map

This file maps Claude `agent teams` semantics to the current `team-c` runtime.

| Claude concept | Team-C runtime |
|---|---|
| shared task list | `docs/research/team-c-codex/<team>/task-board.json` + `task-board.md` |
| teammate direct messaging | `docs/research/team-c-codex/<team>/mailbox.jsonl` + `mailbox.md` |
| lead ask triage | `ask-lead` + `lead-triage` with triage bucket + lead reply artifact + task note/broadcast linkage |
| lead/teammate lifecycle | `docs/research/team-c-codex/<team>/team.json` teammate states + lifecycle commands |
| plan approval | `plan-request`, `plan-approve`, `plan-reject`, optional `--leader-plan-approval auto` |
| cleanup semantics | `cleanup` command, blocked while teammates are active |
| in-process display | `display.py watch` dashboard |
| split panes | `start-split-panes.sh` using tmux |
| claim next | `task-claim-next` |
| ask lead | `ask-lead` |
| inbox cursor / ack | `mail-pop` + `mail-ack` |
| teammate worktree metadata | teammate spec `role[:id[:model[:worktree]]]` |

## Important limitation

This runtime gives you protocol and artifact semantics, not a native Claude transport.

What is implemented:

- explicit state
- explicit coordination artifacts
- explicit cleanup checks
- explicit mailbox entries
- explicit lead ask triage trail
- task assignment mailbox events on owner changes
- triage-linked task notes and shared lead broadcasts for approval/routing
- explicit plan states
- optional leader-side auto plan approval with request/response mailbox trail
- explicit dashboard rendering

What is still emulated rather than native:

- automatic teammate transport
- native UI pane ownership
- native direct peer sockets
- native task-claim race handling across separate long-lived processes

Those gaps are acceptable for a workspace-backed orchestration layer, but they are not identical to Claude's built-in runtime.
