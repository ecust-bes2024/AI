# Mailbox

## M1 [open]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T02:58:15.982599+00:00`
- subject: Task assigned: T1
- kind: `task_assignment`

task: `T1`
title: Review runtime
assigned_by: `lead`
status: `pending`

## M2 [open]

- sender: `lead`
- recipient: `qa`
- sent_at: `2026-04-01T02:58:16.029077+00:00`
- subject: Task assigned: T1
- kind: `task_assignment`

task: `T1`
title: Review runtime
assigned_by: `lead`
status: `pending`

## M3 [resolved]

- sender: `reviewer`
- recipient: `lead`
- sent_at: `2026-04-01T02:58:16.077117+00:00`
- subject: Need approval for T1
- kind: `ask_lead`

Can I widen scope for T1?

## M4 [open]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T02:58:16.124546+00:00`
- subject: Lead triage: approval for M3
- kind: `lead_triage`

source_message: `M3`
bucket: `approval`
lead_decision: Approved within current task boundaries. Update shared artifacts before widening scope.
subject: Need approval for T1

## M5 [open]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T02:58:16.124762+00:00`
- subject: Lead update: approval
- kind: `lead_broadcast`

source_message: `M3`
bucket: `approval`
task: `T1`
subject: Need approval for T1

## M6 [open]

- sender: `lead`
- recipient: `qa`
- sent_at: `2026-04-01T02:58:16.124769+00:00`
- subject: Lead update: approval
- kind: `lead_broadcast`

source_message: `M3`
bucket: `approval`
task: `T1`
subject: Need approval for T1
