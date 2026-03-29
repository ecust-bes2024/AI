# Claude Agent Teams Reference

This file captures the minimum official semantics that `team-c` is meant to preserve.

## Core model

- `agent teams` coordinate multiple Claude Code instances as one team.
- One session acts as `team lead`.
- Teammates work independently in separate context windows.
- Teammates can communicate directly.
- The team shares a task list.

## Official differences from subagents

- subagents: report only to the caller
- agent teams: teammates can coordinate with each other
- subagents: lower token cost
- agent teams: higher token cost, more coordination overhead

## Official usage fit

Best fits:

- research and review
- cross-layer work
- competing hypotheses in debugging
- independent feature slices

Poor fits:

- sequential tasks
- same-file edits
- tightly coupled work with many dependencies

## Official controls

- experimental flag required: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- display modes: `in-process` and `split panes`
- teammates can be assigned tasks or self-claim tasks
- plan approval can be required before implementation
- teammates can be shut down explicitly
- the team should be cleaned up explicitly

## Official communication semantics

- automatic message delivery
- idle notifications
- shared task list
- `message` to a teammate
- `broadcast` to the team

## Official context semantics

- each teammate has its own context window
- teammates load normal project context such as `CLAUDE.md`, MCP servers, and skills
- the lead's conversation history is not inherited

## Practical implication for Team-C

If the runtime cannot provide:

- a lead
- teammates
- a shared task list
- explicit messaging semantics
- explicit cleanup

then `team-c` must either emulate them visibly or say that strict Claude-style semantics cannot be met.

