# Hooks-Codex Output Contract

Prefer JSON-only output.

## Minimal allow

```json
{"ok": true}
```

## Minimal deny

```json
{"ok": false, "reason": "Shell writes outside the allowed repo root."}
```

## Optional fields

```json
{
  "ok": true,
  "decision": "allow",
  "reason": "",
  "additionalContext": "Remember to keep changes inside the assigned worktree.",
  "updatedInput": {
    "cmd": "pytest tests/auth -q"
  }
}
```

## Field meanings

- `ok`
  - boolean pass/fail result
- `decision`
  - `allow`, `deny`, or `ask`
- `reason`
  - short blocking or decision explanation
- `additionalContext`
  - text to append to the next reasoning step
- `updatedInput`
  - rewritten tool input for deterministic transformations

## Rules

- Keep output machine-readable.
- Do not mix human prose with JSON.
- If blocking, always include a short `reason`.
- Only use `updatedInput` for deterministic rewrites.

