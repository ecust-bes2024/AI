# Local Team Skill Notes

Source:

- `/Users/jerry_hu/AI/research/auto-company/.claude/skills/team/SKILL.md`

## Preserved ideas

- choose a temporary team based on task shape
- use a small roster, not maximum headcount
- keep a clear collaboration chain
- have a lead coordinate and synthesize
- store role outputs in predictable locations

## Claude-specific assumptions removed in Team-Codex

- `.claude/agents/` as the source of role definitions
- Claude `Task` / `TaskCreate` wording
- native `team lead` / `teammate` runtime semantics
- native team cleanup semantics

## Practical Codex adaptation

- role prompts are embedded directly in teammate tasks
- `spawn_agent` replaces `Task`
- ownership boundaries replace implicit shared coordination
- lead-mediated routing replaces direct teammate mailbox semantics

