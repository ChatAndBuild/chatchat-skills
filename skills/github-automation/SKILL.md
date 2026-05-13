---
id: github-automation
name: GitHub Automation
description: Use this skill when automating GitHub workflows for issues, pull requests, labels, releases, repository hygiene, or operational guardrails around GitHub actions and repository maintenance.
category: DevOps
---

# GitHub Automation

Coordinate repeatable GitHub operations with consistent quality and low operational risk.

## When to Use

- You need structured automation for repository operations.
- You want consistent issue and PR lifecycle handling.
- You need clear safeguards before merges or bulk updates.

## GitHub Actions Patterns

- **workflow_dispatch:** Add `workflow_dispatch` with `inputs` for manual runs (e.g., cleanup, bulk label, release). Use `input` types (string, boolean, choice) to scope targets and dry-run mode.
- **Scheduled workflows:** Use `schedule` (cron) for periodic cleanup (stale issues, branch pruning, dependency checks). Prefer off-peak times and ensure idempotency.
- **Reusable workflows:** Extract shared logic into `.github/workflows/reusable-*.yml` and call via `workflow_call`. Pass inputs and secrets explicitly; avoid implicit env.
- **Composite actions:** Bundle multi-step logic in `action.yml` under `.github/actions/` for reuse across workflows. Use `runs.using: composite` and document inputs/outputs.

## Automation Recipes

- **Auto-assign reviewers:** Use CODEOWNERS plus `pull_request` trigger; or a custom action that assigns based on file paths, author, or round-robin. Limit to 2-3 reviewers to avoid noise.
- **Auto-label PRs by path:** Match `paths` in `pull_request` and apply labels (e.g., `docs` for `docs/**`, `frontend` for `src/web/**`). Combine with type labels from PR title/body.
- **Stale issue/PR management:** Run weekly; comment on inactive items, then close after grace period. Exempt labels like `pinned`, `security`. Log actions for audit.
- **Release draft automation:** On tag push or `workflow_dispatch`, generate changelog from commits/PRs, create GitHub Release draft, attach artifacts. Require manual publish.

## Common Pitfalls

- **Over-automation causing noise:** Too many comments, labels, or notifications. Consolidate actions, batch updates, and use "quiet" options where available.
- **Workflows without permissions scoping:** Using `permissions: write-all` or broad tokens. Prefer least-privilege: `contents: read`, `issues: write` only when needed, and `id-token` for OIDC where applicable.
- **Missing concurrency controls:** Parallel runs overwriting each other. Add `concurrency: group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress` (or `false`) as appropriate.
- **Not testing workflows in dry-run:** Run with `--dry-run` or a `dry_run` input that skips mutations. Test on a fork or branch before merging to main.

## Workflow

1. Identify repository objective (triage, release flow, contributor workflow, cleanup).
2. Define required GitHub entities and actions (issues, PRs, labels, assignees, milestones).
3. Design idempotent steps with precondition checks.
4. Add safety gates for destructive or high-impact operations.
5. Produce an execution plan plus fallback/retry guidance.

## Output Format

```markdown
## Objective
- <goal>

## Automation Design
- Trigger: <push|pull_request|schedule|workflow_dispatch>
- Permissions: <minimal set>
- Concurrency: <group and cancel-in-progress policy>

## Automation Steps
1. <step with precondition>
2. <step with expected outcome>

## Safety Checks
- [ ] Repository/branch context verified
- [ ] Target set reviewed
- [ ] Dry-run or scoped run defined
- [ ] Permissions scoped to minimum required
- [ ] Concurrency group defined

## Failure Handling
- Retry policy: <policy>
- Rollback/undo path: <steps>
- Notification: <where to alert on failure>
```

## Constraints

- Prefer scoped, reversible actions over broad changes.
- Validate repository and branch context before acting.
- Flag any ambiguous intent instead of guessing.