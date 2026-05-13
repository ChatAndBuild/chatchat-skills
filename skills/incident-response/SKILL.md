---
id: incident-response
name: Incident Response
description: Use this skill when leading or structuring incident response, including triage, containment, communications, recovery, severity assessment, timelines, and post-incident follow-up.
category: DevOps
---

# Incident Response

Coordinate incident handling so teams can reduce impact and restore service safely.

## When to Use

- A production issue is actively affecting users or service reliability.
- You need a structured sequence for triage, containment, and recovery.
- You need clear communications during an ongoing incident.

## Severity Classification Matrix

- **SEV1**: Critical. Full outage or data loss. All hands, 24/7 response. Executive visibility.
- **SEV2**: Major. Significant degradation or partial outage. On-call + escalation. Customer impact visible.
- **SEV3**: Minor. Degraded performance, workaround exists. Standard on-call. Limited customer impact.
- **SEV4**: Low. Cosmetic or isolated. Ticket-based. No immediate user impact.

Reassess severity as new information emerges. Downgrade only when impact is confirmed reduced.

## Incident Management Techniques

### Communication Templates

**Initial blast**: "We are investigating [brief symptom]. Impact: [who/what]. ETA for next update: [time]. Status page: [link]."

**Progress update**: "Update [time]: [what we found]. Current action: [containment/recovery step]. Next update: [time]."

**Resolution**: "Resolved at [time]. Root cause: [one line]. Follow-up: [postmortem, fixes]. We apologize for the impact."

Keep updates factual, time-bounded, and free of blame. Avoid speculation.

### War Room Coordination

Designate roles immediately. Use a single channel (Slack, Teams) for incident traffic. Commander drives decisions; scribe logs timeline and actions; communications owns external updates. Run short syncs (e.g., every 15 min) to align. Document every decision with timestamp and rationale.

### Blameless Postmortem Structure

1. **Summary**: What happened, impact, duration.
2. **Timeline**: Chronological events with timestamps.
3. **Root cause**: Technical cause and contributing factors.
4. **What went well**: Detection, response, collaboration.
5. **What we'll improve**: Action items with owners and deadlines.
6. **Lessons learned**: Process or technical changes to prevent recurrence.

Focus on systems and process, not individuals. Assign owners to every action item.

## Role-Specific Responsibilities

- **Incident Commander**: Owns decisions, prioritizes containment over diagnosis, delegates tasks, calls escalations. Does not perform deep technical work during active incident.
- **Communications Lead**: Drafts and publishes status updates, manages stakeholder expectations, ensures consistent messaging. Does not speculate on root cause publicly.
- **Responder**: Executes technical actions (runbooks, rollbacks, config changes). Reports findings to commander. Does not make unilateral changes outside runbook without commander approval.
- **Scribe/Observer**: Logs timeline, decisions, and actions in real time. Captures context for postmortem. Does not participate in technical decisions.
- **Subject Matter Expert**: Provides domain knowledge when escalated. Advises commander. May join as responder if needed.

## Workflow

1. Define incident scope, severity, and current impact.
2. Assign incident roles (commander, communications, responder, observer/scribe).
3. Stabilize service with immediate containment actions.
4. Investigate probable root cause while protecting availability.
5. Recover service and verify user-impact metrics return to baseline.
6. Capture timeline, decisions, and follow-up actions.

## Common Pitfalls

- **Skipping containment for diagnosis**: Diving into root cause before stopping the bleed. Contain first, diagnose second. Users care about restoration, not perfect understanding.
- **Hero culture**: Single person owning the incident without delegation. Creates bottleneck and burnout. Rotate responders, document for handoff.
- **Poor handoffs between shifts**: Incomplete context, missing timeline, unclear next steps. Use written handoff: current state, actions taken, open hypotheses, next actions.
- **Incomplete timelines**: Gaps in the timeline obscure causality. Scribe must log continuously; backfill from logs/chat if needed.
- **No postmortem follow-through**: Postmortem written but action items never completed. Assign owners and deadlines; track in project management; review in next incident prep.

## Output Format

```markdown
## Incident Summary
- Severity: <SEV1-4>
- Impact: <user/system impact>
- Start time: <timestamp>
- Commander: <name>
- Communications: <name>

## Active Actions
- [ ] Containment action
- [ ] Recovery action
- [ ] Verification action

## Communications
- Stakeholders: <who was informed>
- Latest status: <current status>
- Next update ETA: <time>
- Status page updated: <yes/no>

## Timeline (key events)
- <time>: <event>
- <time>: <event>

## Handoff (if shifting)
- Current state: <summary>
- Actions taken: <list>
- Open hypotheses: <list>
- Next actions: <list>

## Follow-up
- Root cause hypothesis: <summary>
- Permanent fixes: <list>
- Postmortem owner/date: <owner + target date>
- Action items: <owner, deadline>
```

## Constraints

- Prioritize impact reduction over perfect diagnosis early in the incident.
- Keep status updates factual and time-bounded.
- Record assumptions and decisions for postmortem accuracy.
