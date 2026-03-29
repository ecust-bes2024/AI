# Lead Ask Triage

This file defines how the team lead should handle `ask-lead` messages.

## Goal

Make `ask-lead` operationally consistent instead of improvisational.

## When a teammate asks the lead

The lead should classify the request into one of four buckets:

1. `approval`
   - scope expansion
   - plan approval
   - dependency acceptance
   - risk acceptance

2. `clarification`
   - missing requirement
   - ambiguous interface
   - unclear ownership

3. `routing`
   - another teammate owns the answer
   - the answer should be broadcast
   - the task board must be updated first

4. `escalation`
   - human decision required
   - protocol conflict
   - blocker that should stop downstream work

## Default lead actions

### approval

- answer explicitly
- if scope or plan changes, update the task board
- if a decision affects multiple teammates, broadcast it

### clarification

- answer directly if local context is enough
- otherwise route to the owning teammate and record the outcome

### routing

- relay the question or answer via mailbox
- avoid private resolution when the result changes shared execution

### escalation

- stop claiming equivalence with the plan
- mark the blocker clearly
- ask the human partner

## Required follow-through

After responding to `ask-lead`, the lead should decide whether to also:

- update `task-board.md`
- send a mailbox reply
- send a broadcast
- update `lead-summary.md`

If the answer changes execution, at least one shared artifact must be updated.

