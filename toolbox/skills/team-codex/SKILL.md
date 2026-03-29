---
name: "team-codex"
description: "Use when the user wants a Codex-native team workflow with parallel subagents, explicit specialist roles, lead synthesis, and a practical adaptation of a Claude-style team orchestration pattern."
---

# Team-Codex

Use this skill when the user explicitly wants delegation, parallel specialists, or a team workflow inside Codex.

This skill adapts the local Claude `team` skill into something the current Codex environment can actually execute.

## Design goal

Keep the valuable structure from the local Claude workflow:

- pick a small specialist team
- give each teammate a concrete role
- assign distinct work
- collect written deliverables
- synthesize as a lead

Do not pretend Codex has Claude's native `agent teams` protocol. Use Codex-native primitives instead.

## Runtime assumptions

In Codex, the practical building blocks are:

- `spawn_agent`
- `send_input`
- `wait_agent`
- `close_agent`
- `multi_tool_use.parallel`

Codex does not provide a native Claude-style shared task list or direct teammate-to-teammate mailbox by default. Emulate coordination through:

- explicit ownership
- lead-mediated routing
- shared workspace artifacts when useful

When you need those artifacts, use the `team-c` runtime in the sibling skill:

- `../team-c/scripts/init-team.sh`
- `../team-c/scripts/task-board.sh`
- `../team-c/scripts/mailbox.sh`
- `../team-c/scripts/lifecycle.sh`

## Trigger rule

Only spawn teammates when the user explicitly asks for:

- `team`
- `team-codex`
- delegation
- subagents
- parallel agent work

If the user only wants analysis or a normal implementation, stay single-threaded.

## Team structure

### Lead

The lead stays in the main thread and owns:

- role selection
- task design
- teammate prompts
- integration
- final answer

The lead should not duplicate delegated work.

### Teammates

Pick `2-5` teammates from the role roster in:

- [references/role-roster.md](references/role-roster.md)

Prefer the minimum team that closes the workflow.

Examples:

- product + architecture + critic
- fullstack + QA
- research + marketing + finance

## Codex workflow

1. Analyze the task.
2. Select `2-5` necessary roles.
3. Announce the team briefly and why each role is needed.
4. Define disjoint scopes and concrete deliverables.
5. Create a workspace artifact area if the task is large:
   - `docs/team-codex/<team-name>/`
   - if strict coordination is needed, also initialize `docs/team-c/<team-name>/` via the `team-c` runtime
6. Spawn teammates with role prompt + task prompt + ownership boundaries.
7. Keep the lead busy with non-overlapping work while teammates run.
8. Wait only when integration is blocked on a result.
9. Synthesize teammate outputs into one plan, answer, or implementation.
10. Close teammates when done.

## Deliverable convention

For substantial team runs, prefer:

- `docs/team-codex/<team-name>/brief.md`
- `docs/team-codex/<team-name>/task-board.md`
- `docs/team-codex/<team-name>/<role>.md`
- `docs/team-codex/<team-name>/summary.md`

Use artifacts when they reduce ambiguity. Do not create them for trivial tasks.

If you need stricter team semantics, initialize the shared protocol artifacts:

```bash
../team-c/scripts/init-team.sh <team-name> --lead lead --mode in-process --teammate architect --teammate reviewer
```

## Prompt contract for each teammate

Each teammate prompt should include:

- the assigned role
- the exact task
- files or modules they own
- files they must not overwrite casually
- expected output format
- whether they should edit files directly or only analyze
- the reminder that other teammates may also be working in parallel

## Coordination rules

- Assign explicit ownership to avoid merge conflicts.
- Use the lead as the default relay point.
- If two teammates need to influence each other, the lead should pass the relevant result across.
- Prefer independent slices over conversational ping-pong between teammates.

## Mapping from the local Claude team skill

This skill preserves these ideas from the local Claude `team` skill:

- role-based staffing
- temporary team assembly
- lead-driven coordination
- per-role outputs
- final synthesis for the founder/user

This skill intentionally changes these parts:

- replaces Claude `Task` spawning with Codex `spawn_agent`
- replaces native teammate messaging with lead-mediated coordination
- replaces implicit team resources with explicit workspace artifacts only when needed
- replaces Claude-specific `.claude/agents/` assumptions with an embedded role roster

## What not to do

- Do not spawn a large team by default.
- Do not assign overlapping ownership unless it is a deliberate review pattern.
- Do not wait idly for long-running teammates without doing integration or verification work.
- Do not claim Claude `agent teams` equivalence. This is a Codex adaptation, not the same protocol.

## Recommended patterns

### 1. Parallel review

- one teammate on security
- one on performance
- one on tests
- lead merges findings

### 2. Product-to-build chain

- one teammate on product framing
- one on architecture
- one on implementation
- one on QA

### 3. Research swarm

- multiple researchers on independent hypotheses
- one critic to attack assumptions
- lead consolidates

## Reference

Read these only when needed:

- [references/role-roster.md](references/role-roster.md)
- [references/local-team-skill-notes.md](references/local-team-skill-notes.md)
