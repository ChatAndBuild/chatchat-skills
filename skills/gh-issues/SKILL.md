---
id: gh-issues
name: GH Issues
description: Use this skill when managing GitHub issues with structured triage, prioritization, assignment, labels, status tracking, duplicates, and actionable next steps.
category: Development
---

# GH Issues

Operate issue workflows so backlog health and ownership stay clear.

## When to Use

- You need to organize and prioritize GitHub issues.
- You need consistent labeling and assignment conventions.
- You want to reduce stale or ambiguous backlog items.

## Triage Patterns

**Label taxonomy.** Use a flat or hierarchical scheme: `type` (bug, feature, chore, docs), `priority` (P0/P1/P2 or critical/high/medium/low), `status` (backlog, in-progress, blocked, done), and `area` (frontend, backend, infra, docs). Avoid overlapping labels (e.g., don't mix "urgent" and "P0"). Define each label in the repo description so triagers use them consistently.

**SLA by priority.** Tie response and resolution targets to priority: e.g., P0 triaged within 24h and resolved within 1 week; P1 within 3 days and 2 weeks; P2 within 1 week and 1 sprint. Document SLAs in CONTRIBUTING or a triage doc and enforce via automation or weekly review.

**Template enforcement.** Require issue templates for bug reports and feature requests. Templates should capture: environment, steps to reproduce, expected vs actual behavior, and acceptance criteria. Use GitHub's template chooser and validate that new issues include required sections before labeling.

## Backlog Health Indicators

- **Stale issue age:** Issues with no activity for 30-90 days (configurable). Flag for triage: close, update, or move to backlog.
- **Unassigned rate:** Share of open issues without an assignee. High unassigned rate suggests unclear ownership or overload.
- **Duplicate rate:** Issues marked as duplicate or with similar titles/descriptions. High rate indicates weak search before filing or missing templates.

Track these weekly and set thresholds (e.g., &lt;20% unassigned, &lt;10% stale) to trigger triage sessions.

## Automation Patterns

- **Auto-label from templates:** Use GitHub Actions or Probot to apply labels based on template choice or body keywords (e.g., "bug" template -> `type: bug`).
- **Stale bot configuration:** Configure Stale bot with grace period (e.g., 60 days), exempt labels (e.g., `pinned`, `roadmap`), and a clear comment before closing. Avoid closing high-priority issues automatically.
- **Milestone-based tracking:** Assign issues to milestones for releases or quarters. Use automation to move issues when milestones change or to close stale milestones.

## Common Pitfalls

- **Label sprawl:** Too many ad-hoc labels (e.g., "needs-review", "needs-review-urgent") without a taxonomy. Consolidate into a small, well-defined set.
- **No priority definition:** "High" and "critical" used interchangeably. Define and document what each priority means and who can set it.
- **Issues without acceptance criteria:** Feature requests and bugs lack clear done conditions. Require acceptance criteria in templates and reject or send back incomplete issues.
- **Orphaned issues after team changes:** When people leave, reassign or close their issues. Use automation to detect long-unassigned issues and surface them in triage.

## Workflow

1. Categorize issues by type, priority, and ownership.
2. Apply consistent labels and milestones.
3. Identify blocked, stale, and duplicate issues.
4. Propose next actions for each issue bucket.
5. Track follow-up cadence and closure criteria.

## Output Format

```markdown
## Triage Summary
- Total open issues: <count>
- High priority: <count>
- Unassigned: <count>
- Stale (>N days): <count>
- Duplicate candidates: <count>

## Backlog Health
- Unassigned rate: <percent>
- Stale rate: <percent>
- Label coverage: <percent> (issues with type/priority/area)

## Recommended Actions
- [ ] Assign owners to unassigned critical issues
- [ ] Label and prioritize new issues
- [ ] Close or merge duplicates
- [ ] Mark stale candidates for follow-up
- [ ] Update or close orphaned issues

## Per-Issue Notes (for flagged items)
- #<num>: <brief note and suggested action>
```

## Constraints

- Keep labels and priority definitions consistent.
- Prefer explicit ownership and next action on every active issue.
- Do not close issues without a stated reason.
