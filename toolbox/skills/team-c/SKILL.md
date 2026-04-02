---
name: "team-c"
description: "Use when the user explicitly wants Claude Code-style agent teams semantics, a strict team-lead plus teammates workflow, or an exact team protocol rather than a loose subagent fan-out."
---

# Team-C

Use this skill only when the user explicitly wants a Claude Code-style team workflow.

This skill is strict on semantics. Do not silently downgrade `agent teams` into ordinary one-shot subagents.

`team-c` now includes a runnable artifact-backed runtime under `scripts/`. Use it whenever you need to materialize the protocol inside a workspace.

## What must be preserved

`team-c` preserves these Claude `agent teams` concepts:

- one `team lead`
- multiple independent `teammates`
- one shared task list
- teammate-to-teammate communication semantics
- explicit task states: `pending`, `in_progress`, `completed`
- optional plan-approval before implementation
- explicit teammate shutdown and team cleanup

If a requested execution environment cannot support one of these directly, state the gap and say whether you will:

- emulate it with artifacts and lead-mediated coordination
- or stop because strict semantics would be misleading

## When to use

Use `team-c` when:

- the user explicitly asks for `Claude team`, `agent teams`, `team-c`, or a strict Claude-style multi-agent workflow
- the task benefits from parallel exploration, review, or independent workstreams
- the user wants a real lead-plus-team structure, not just multiple independent answers

Do not use it for:

- single-file edits
- tightly sequential work
- tasks where all workers would fight over the same files
- situations where only the final answer matters and teammate coordination adds no value

## Required operating model

### 1. Team lead

The lead owns:

- team creation
- role selection
- task decomposition
- assignment and dependency management
- message routing when native peer messaging is unavailable
- final synthesis
- shutdown and cleanup

### 2. Teammates

Each teammate must have:

- its own role
- its own task scope
- its own deliverable
- its own context boundary

Teammates should not be given overlapping ownership unless the overlap is intentional and review-oriented.

### 3. Shared task list

Maintain a visible task board for the whole team. If the runtime lacks a native shared task list, emulate one in a workspace artifact.

Recommended path:

`docs/research/team-c-codex/<team-name>/task-board.md`

Use this schema:

```markdown
| task_id | title | owner | status | depends_on | deliverable |
|---|---|---|---|---|---|
| T1 | ... | ... | pending | - | ... |
```

Allowed statuses:

- `pending`
- `in_progress`
- `completed`

Use the runtime instead of hand-editing when possible:

```bash
./scripts/task-board.sh task-add <team-name> "Review auth flow" --owner reviewer --deliverable reviewer.md
./scripts/task-board.sh task-update <team-name> T1 --status in_progress
./scripts/task-board.sh task-claim-next <team-name> reviewer
./scripts/task-board.sh task-claim <team-name> T2 reviewer
```

### 4. Mailbox

Claude `agent teams` allow direct teammate communication. If the runtime does not support true peer messaging, emulate a mailbox and have the lead relay messages.

Recommended path:

`docs/research/team-c-codex/<team-name>/mailbox.md`

Each message should record:

- sender
- recipient
- timestamp
- subject
- body
- resolution status

Use the runtime mailbox helpers:

```bash
./scripts/mailbox.sh mail-send <team-name> --sender lead --recipient reviewer --subject "Clarify finding" --body "Check the token refresh path too."
./scripts/mailbox.sh mail-send <team-name> --sender reviewer --recipient architect --subject "Need interface detail" --body "Which adapter owns session rotation?"
./scripts/mailbox.sh ask-lead <team-name> --sender reviewer --subject "Need approval" --body "Can I widen the task scope?"
./scripts/mailbox.sh lead-triage <team-name> --task-id T2 --set-status pending --add-depends-on T1
./scripts/mailbox.sh mail-sync <team-name> --recipient reviewer
./scripts/mailbox.sh mail-pop <team-name> --recipient lead
./scripts/mailbox.sh mail-ack <team-name> ACK-1
./scripts/mailbox.sh mail-resolve <team-name> M2
```

Lead-side handling guidance for `ask-lead` lives in:

- [references/lead-ask-triage.md](references/lead-ask-triage.md)

Task ownership changes also emit `task_assignment` mailbox entries, so assignment is visible in shared artifacts instead of living only in the task board.

`lead-triage` now also:

- writes a triage note into the related task when `--task-id` is provided or a `T<number>` reference can be inferred from the ask
- emits `lead_broadcast` mailbox updates for `approval` and `routing` buckets so shared execution changes are visible to the team
- can directly mutate task rules with `--set-owner`, `--set-status`, `--add-depends-on`, `--remove-depends-on`, and `--clear-depends-on`

`mail-sync` now lets a teammate consume mailbox effects into shared artifacts:

- `task_assignment` updates teammate heartbeat/state and can move a ready task to `in_progress`
- `lead_broadcast` / `lead_triage` can move owned tasks between `pending` and `in_progress` based on the broadcast bucket
- `plan_approval_response` updates teammate state and task status when approval is granted

### 5. Plan approval

For risky work, the lead may require a teammate to stay in planning mode until a plan is approved.

When used, the lead must define explicit approval criteria such as:

- tests included
- no schema changes
- rollback path exists

Do not start implementation before plan approval is granted.

If you want Claude Code-style leader-side auto-approval semantics, initialize the team with `--leader-plan-approval auto`. That keeps the request/response trail in artifacts while letting the lead runtime auto-approve teammate plan requests.

Use the runtime plan flow:

```bash
./scripts/init-team.sh my-team --lead lead --mode in-process --teammate architect --leader-plan-approval auto
./scripts/task-board.sh plan-request <team-name> T2 ./plans/auth-plan.md --note "Ready for lead review"
./scripts/task-board.sh plan-approve <team-name> T2 --note "Approved if tests remain in scope"
./scripts/task-board.sh plan-reject <team-name> T2 --note "Reduce database blast radius"
```

### 6. Cleanup

At the end, the lead must:

- ask teammates to stop
- verify no active work is still running
- mark the final board state
- write a final synthesis
- archive or remove temporary team artifacts if requested

Use the lifecycle runtime:

```bash
./scripts/lifecycle.sh set-state <team-name> reviewer idle
./scripts/lifecycle.sh heartbeat <team-name> reviewer --note "Review complete, waiting for feedback"
./scripts/lifecycle.sh cleanup <team-name>
```

## Execution workflow

1. Decide whether the task is a real team candidate.
2. Name the team in short `kebab-case`.
3. Define lead, teammates, and distinct scopes.
4. Create the shared task board.
5. Create mailbox and synthesis artifact paths.
6. Spawn or assign teammates only after ownership is clear.
7. Keep the lead focused on coordination and synthesis, not duplicate implementation.
8. If teammates need to coordinate, route via native team messaging or the mailbox artifact.
9. Require plan approval when risk justifies it.
10. Shut down teammates and clean up explicitly.

## Runtime

The runtime lives in:

- `scripts/team_runtime.py`
- `scripts/display.py`
- shell wrappers in `scripts/*.sh`

### Dependency check

Run:

```bash
./scripts/check-deps.sh
```

This checks:

- `python3`
- optional `tmux`
- runtime script compilation
- global skill install path state

### Smoke test

Run:

```bash
./scripts/smoke-test.sh
```

By default it writes a disposable validation run under:

`/Users/jerry_hu/AI/sandbox/docs/team-c-codex-smoke/`

### Create a team

```bash
./scripts/init-team.sh my-team --lead lead --mode in-process --teammate architect:architect::true --teammate reviewer --teammate qa --require-plan-approval --leader-plan-approval auto
```

Teammate format:

```text
role[:id[:model[:worktree]]]
```

Examples:

- `architect`
- `reviewer:security-reviewer`
- `implementer:worker:gpt-5.4-mini:true`

This creates:

- `docs/research/team-c-codex/<team-name>/team.json`
- `docs/research/team-c-codex/<team-name>/task-board.json`
- `docs/research/team-c-codex/<team-name>/task-board.md`
- `docs/research/team-c-codex/<team-name>/mailbox.jsonl`
- `docs/research/team-c-codex/<team-name>/mailbox.md`
- `docs/research/team-c-codex/<team-name>/lead-summary.md`
- `docs/research/team-c-codex/<team-name>/runtime/logs/*.log`

### In-process display

Use the dashboard watcher:

```bash
python3 ./scripts/display.py watch <team-name>
```

### Split-pane display

Use tmux panes for dashboard plus teammate logs:

```bash
./scripts/start-split-panes.sh <team-name>
```

This is an emulation of Claude split panes, not a native Codex UI surface.

## Deliverables

Unless the user specifies otherwise, use:

- `docs/research/team-c-codex/<team-name>/task-board.md`
- `docs/research/team-c-codex/<team-name>/mailbox.md`
- `docs/research/team-c-codex/<team-name>/lead-summary.md`
- `docs/research/team-c-codex/<team-name>/<teammate-role>.md`

## Best practices

- Choose the smallest useful team.
- Prefer independent work slices.
- Start with research, review, or architecture before parallel code edits.
- Avoid file conflicts by assigning ownership explicitly.
- Do not claim Claude-style semantics if you are only doing plain fan-out.

## Reference

For the exact Claude `agent teams` model and constraints, read:

- [references/claude-agent-teams.md](references/claude-agent-teams.md)
- [references/runtime-feature-map.md](references/runtime-feature-map.md)
