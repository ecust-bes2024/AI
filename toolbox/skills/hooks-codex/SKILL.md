---
name: "hooks-codex"
description: "Use when designing or implementing a Codex hook system, command-style hook handlers, skill-scoped hooks, or hook-like policy and workflow gates inspired by Claude Code-style lifecycle events."
---

# Hooks-Codex

Use this skill when the goal is to design, implement, or validate a Codex-compatible hook layer.

This is not a full native hooks runtime. It is a minimal lab scaffold for:

- event model design
- handler contract design
- command hook prototyping
- skill-scoped hook design
- policy and workflow gate experiments

## Current scope

`hooks-codex` is intentionally narrow.

It currently focuses on:

- `pre_tool_use`
- `permission_request`
- `subagent_start`
- `task_completed`
- `lead_reply`
- `worktree_create`
- `worktree_remove`

Do not expand to every possible event unless there is a concrete need.

## Goals

1. Keep the event model explicit.
2. Keep handler contracts stable.
3. Prefer command hooks first.
4. Add prompt or agent handlers only when the command path is insufficient.
5. Keep platform-neutral semantics separate from platform-specific execution details.

## Deliverables

When using this skill, prefer producing one or more of:

- a hook config snippet
- a command hook script
- a payload schema
- a blocking policy rule
- a design note for a new event

## Event model

Read:

- [references/event-model.md](references/event-model.md)
- [references/output-contract.md](references/output-contract.md)

## Templates

Start from:

- [templates/hooks-codex.example.toml](templates/hooks-codex.example.toml)
- [templates/pre_tool_use.py](templates/pre_tool_use.py)
- [templates/task_completed.py](templates/task_completed.py)

## Lab entry point

The lab default config and wrapper live in:

- [config/hooks-codex.lab.toml](config/hooks-codex.lab.toml)
- [scripts/lab-dispatch.sh](scripts/lab-dispatch.sh)
- [scripts/guarded-shell.sh](scripts/guarded-shell.sh)

Example:

```bash
./scripts/lab-dispatch.sh --event pre_tool_use --payload-json '{"hook_event_name":"PreToolUse","tool_name":"shell","tool_input":{"cmd":"git status"},"cwd":"/tmp","session_id":"demo"}'
```

For a real command path in the lab, use:

```bash
./scripts/guarded-shell.sh git status
```

## Rules

- Treat hooks as policy and orchestration boundaries, not as a substitute for normal application logic.
- Block sparingly and explicitly.
- Prefer deterministic command hooks before model-mediated hooks.
- Keep all output JSON-only when the handler is intended to be machine-consumed.
- Separate:
  - event schema
  - handler behavior
  - policy decision

## Recommended progression

1. Define the event and payload.
2. Decide whether the event can block.
3. Decide the minimum handler type needed.
4. Prototype with a command hook.
5. Add richer handlers only if required.

## Validation

Run:

```bash
./scripts/check-deps.sh
```

Use the templates as executable examples before designing new handlers from scratch.
