# Task Board

| task_id | title | owner | status | depends_on | plan | deliverable |
|---|---|---|---|---|---|---|
| T1 | Evaluate runtime design and protocol fidelity | architect | completed | - | not_required | architect.md |
| T2 | Attack semantic gaps and misleading equivalence | critic | completed | - | not_required | critic.md |
| T3 | Assess usability, installability, and operational risk | qa | completed | - | not_required | qa.md |

## Notes

- `T1` Evaluate runtime design and protocol fidelity
  owner: architect
  status: completed
  notes: Assess team-c runtime against the declared team protocol and identify what is already usable.
- `T2` Attack semantic gaps and misleading equivalence
  owner: critic
  status: completed
  notes: Identify where team-c still diverges from Claude agent teams and what claims should be softened.
- `T3` Assess usability, installability, and operational risk
  owner: qa
  status: completed
  notes: Focus on real usage friction, install path, runtime dependencies, and missing checks.
