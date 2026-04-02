# Task Board

| task_id | title | owner | status | depends_on | plan | deliverable |
|---|---|---|---|---|---|---|
| T1 | Review runtime | reviewer | pending | T2 | approved | - |
| T2 | Secondary work | qa | in_progress | - | not_required | - |

## Notes

- `T1` Review runtime
  owner: reviewer
  status: pending
  plan_note: ready
  notes: [lead-triage M3] bucket=approval
[lead-triage M3] rules: depends_on+=T2
[mail-sync M1] task_assignment consumed by reviewer
[mail-sync M4] lead_triage bucket=approval
[mail-sync M5] lead_broadcast bucket=approval
[mail-sync M8] plan_approval_response decision=approved
[mail-sync M6] lead_broadcast bucket=approval
- `T2` Secondary work
  owner: qa
  status: in_progress
  notes: [mail-sync M2] task_assignment consumed by qa
