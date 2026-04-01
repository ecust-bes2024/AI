# Mailbox

## M1 [open]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T02:52:36.790782+00:00`
- subject: Task assigned: T1
- kind: `task_assignment`

task: `T1`
title: Review runtime
assigned_by: `lead`
status: `pending`

## M2 [open]

- sender: `lead`
- recipient: `qa`
- sent_at: `2026-04-01T02:52:36.834005+00:00`
- subject: Task assigned: T1
- kind: `task_assignment`

task: `T1`
title: Review runtime
assigned_by: `lead`
status: `pending`

## M3 [resolved]

- sender: `reviewer`
- recipient: `lead`
- sent_at: `2026-04-01T02:52:36.879528+00:00`
- subject: Need approval
- kind: `ask_lead`

Can I widen scope?

## M4 [open]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T02:52:36.924948+00:00`
- subject: Lead triage: approval for M3
- kind: `lead_triage`

source_message: `M3`
bucket: `approval`
lead_decision: Approved within current task boundaries. Update shared artifacts before widening scope.
subject: Need approval
