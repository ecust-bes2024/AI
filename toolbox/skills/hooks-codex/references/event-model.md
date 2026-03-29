# Hooks-Codex Event Model

This file defines the minimum event surface for the current hooks-codex scaffold.

## Phase 1 events

### `pre_tool_use`

Purpose:

- inspect an about-to-run tool
- optionally block
- optionally annotate the next turn

Suggested payload:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "shell",
  "tool_input": {"cmd": "git push"},
  "cwd": "/abs/path",
  "session_id": "..."
}
```

### `permission_request`

Purpose:

- apply consistent policy before human approval
- allow / deny / escalate

Suggested payload:

```json
{
  "hook_event_name": "PermissionRequest",
  "tool_name": "shell",
  "tool_input": {"cmd": "rm -rf build"},
  "permission_suggestions": ["allow", "ask"],
  "cwd": "/abs/path"
}
```

### `subagent_start`

Purpose:

- inject guardrails into spawned teammates
- annotate subagent context

Suggested payload:

```json
{
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-123",
  "agent_type": "worker"
}
```

### `task_completed`

Purpose:

- verify completion claims
- append review obligations
- block completion if needed

Suggested payload:

```json
{
  "hook_event_name": "TaskCompleted",
  "task_id": "T1",
  "task_subject": "Implement auth retry",
  "team_name": "my-team",
  "teammate_name": "implementer"
}
```

### `lead_reply`

Purpose:

- make the lead's reply to a teammate observable
- append follow-through context when a lead answer changes execution

Suggested payload:

```json
{
  "hook_event_name": "LeadReply",
  "team_name": "my-team",
  "sender": "lead",
  "recipient": "worker",
  "subject": "Scope approved",
  "body": "You may widen the task to include retry logic."
}
```

### `worktree_create`

Purpose:

- standardize worktree naming and placement
- attach metadata

Suggested payload:

```json
{
  "hook_event_name": "WorktreeCreate",
  "name": "feature-auth"
}
```

### `worktree_remove`

Purpose:

- run cleanup before removing worktree artifacts

Suggested payload:

```json
{
  "hook_event_name": "WorktreeRemove",
  "worktree_path": "/abs/path/to/worktree"
}
```

## Design rule

Do not add new events unless:

- they solve a concrete policy or orchestration problem
- they cannot be expressed with an existing event
