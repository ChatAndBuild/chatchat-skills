---
id: managing-database-recovery
name: Managing Database Recovery
description: Use this skill when designing or reviewing database recovery plans for data loss, corruption, or operational incidents, including backups, RPO/RTO, restore sequencing, and integrity checks.
category: Databases
---

# Managing Database Recovery

Use this skill to design or review recovery plans for data loss, corruption, or operational incidents.

## Clarify First
- Likely incident type such as accidental deletion, corruption, outage, or region loss.
- Recovery time objective and recovery point objective.
- Backup types available and how recently they were validated.
- Whether the system can tolerate partial read-only or degraded modes.
- Which teams and systems depend on the restore sequence.

## Recovery Principles
- Backups are only useful if restores are tested.
- Restoration order matters for dependent services.
- Snapshot age and data-loss tolerance must be explicit.
- A rushed restore without validation can compound the incident.
- Communication and decision points belong in the plan, not only technical steps.

## Good Output
- Incident triage checklist.
- Restore decision tree.
- Validation steps before reopening traffic.
- Risks, assumptions, and fallback options.
- Questions to resolve before an actual incident.

## Common Gaps
- No tested restore path.
- No clarity on point-in-time recovery capabilities.
- No post-restore verification plan.
- Confusing replication with recoverability.
