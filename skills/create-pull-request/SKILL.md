---
id: create-pull-request
name: Create Pull Request
description: Use this skill when preparing GitHub pull requests with clear summaries, scoped changes, test plans, reviewer context, risk notes, and links to relevant issues or evidence.
category: Development
---

# Create Pull Request

Create a reviewer-ready pull request that explains intent, impact, and validation in a clear, compact format.

## When to Use

- You need to open a new GitHub pull request from a feature branch.
- You want a structured PR title/body that helps reviewers quickly understand risk and scope.
- You need a consistent checklist for testing and rollout notes.

## PR Title Best Practices

- Use imperative mood: "Add", "Fix", "Remove", "Refactor" (not "Added", "Fixes").
- Prefix with scope when helpful: `auth: fix token refresh race`, `api: add pagination to list endpoint`.
- Keep under 72 characters for clean git log and UI display.
- Avoid vague titles like "Miscellaneous fixes" or "Various updates"-be specific.

## Description Writing Techniques

- Link related issues: `Fixes #123` or `Related to #45` so reviewers and automation can trace context.
- For UI changes: include before/after screenshots or a short video link; describe what the user sees.
- Call out dependencies: if the PR depends on another PR or deployment, state it explicitly.
- Use checkboxes for test plans so reviewers can verify coverage at a glance.

## Reviewer Selection Guidance

- Respect CODEOWNERS when present; suggested reviewers often auto-populate from it.
- Include domain experts for affected areas (e.g., security for auth changes, infra for deployment).
- Aim for at least the minimum review count required by branch protection; avoid single-reviewer merges for high-risk changes.

## PR Size Guidelines

- Aim for under 400 lines of changed code when possible; larger PRs get less thorough review.
- Split strategy: separate refactors from behavior changes; split large features into logical increments.
- If a PR exceeds 400 lines, add a "Review guide" section pointing reviewers to the most critical files.

## Common Pitfalls

- PRs too large to review: reviewers skim or defer; split into smaller, mergeable units.
- Missing test plan: reviewers cannot verify behavior; always include concrete verification steps.
- Vague "miscellaneous" titles: makes triage and git history useless; use descriptive titles.
- Forgetting to link related issues: breaks traceability and automation.
- Draft vs ready confusion: mark as Draft until ready for review; switch to Ready when tests pass and description is complete.

## Workflow

1. Confirm PR scope from branch changes.
2. Generate a concise title using imperative, scope-prefixed format under 72 chars.
3. Build the PR description using the structure below.
4. Link issues, add screenshots for UI changes, and call out dependencies.
5. Ensure the test plan uses checkboxes and concrete verification steps.
6. Keep wording specific and evidence-based; avoid vague statements.

## Output Format

Use this template:

```markdown
## Summary
- <1-3 bullets describing intent and impact>

## Related Issues
- Fixes #<issue> / Related to #<issue>

## Changes
- <key implementation changes>

## Dependencies
- <other PRs, deployments, or config changes required, or "None">

## Test Plan
- [ ] <test step 1>
- [ ] <test step 2>

## Screenshots / UI (if applicable)
- <description or link to before/after>

## Risks
- <known risk or "None identified">

## Rollback
- <rollback action or "Revert PR">
```

## Constraints

- Prefer short, reviewable bullets over long paragraphs.
- Do not claim tests were run unless explicitly confirmed.
- Keep operational steps explicit when deployment or schema changes are included.