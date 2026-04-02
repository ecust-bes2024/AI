# Mailbox

## M1 [resolved]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T07:50:43.157590+00:00`
- subject: Task assigned: T1
- kind: `task_assignment`

task: `T1`
title: Review runtime
assigned_by: `lead`
status: `pending`

## M2 [resolved]

- sender: `lead`
- recipient: `qa`
- sent_at: `2026-04-01T07:50:43.204648+00:00`
- subject: Task assigned: T2
- kind: `task_assignment`

task: `T2`
title: Secondary work
assigned_by: `lead`
status: `pending`

## M3 [resolved]

- sender: `reviewer`
- recipient: `lead`
- sent_at: `2026-04-01T07:50:43.250650+00:00`
- subject: Need approval for T1
- kind: `ask_lead`

Can I widen scope for T1?

## M4 [resolved]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T07:50:43.297186+00:00`
- subject: Lead triage: approval for M3
- kind: `lead_triage`

source_message: `M3`
bucket: `approval`
lead_decision: Approved within current task boundaries. Update shared artifacts before widening scope.
subject: Need approval for T1

## M5 [resolved]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T07:50:43.297342+00:00`
- subject: Lead update: approval
- kind: `lead_broadcast`

source_message: `M3`
bucket: `approval`
task: `T1`
subject: Need approval for T1

## M6 [resolved]

- sender: `lead`
- recipient: `qa`
- sent_at: `2026-04-01T07:50:43.297351+00:00`
- subject: Lead update: approval
- kind: `lead_broadcast`

source_message: `M3`
bucket: `approval`
task: `T1`
subject: Need approval for T1

## M7 [open]

- sender: `reviewer`
- recipient: `lead`
- sent_at: `2026-04-01T07:50:43.348003+00:00`
- subject: Plan approval requested for T1
- kind: `plan_approval_request`

task: `T1`
title: Review runtime
owner: `reviewer`
plan_file: `approvals/T1-plan.md`
note: ready

## M8 [resolved]

- sender: `lead`
- recipient: `reviewer`
- sent_at: `2026-04-01T07:50:43.348280+00:00`
- subject: Plan approved for T1
- kind: `plan_approval_response`

task: `T1`
decision: `approved`
note: ready
