---
id: changelog-automation
name: Changelog Automation
description: Use this skill when generating or maintaining release changelogs from merged work, including version scope, grouped changes, breaking-change notes, formatting consistency, and verification checks.
category: DevOps
---

# Changelog Automation

Automate changelog creation while keeping release notes accurate and auditable.

## When to Use

- You need consistent release notes across frequent deployments.
- You want changelog entries grouped by meaningful change categories.
- You need a review step to prevent misleading release notes.

## Workflow

1. **Define release scope.** Use git-log-based range detection: `git log <last-tag>..HEAD --oneline` or `git log --since="YYYY-MM-DD"`. Prefer tag-to-HEAD for versioned releases. For date-based ranges, ensure the range is inclusive and timezone-consistent.

2. **Collect and classify changes.** Parse conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `chore:`, `BREAKING CHANGE:`) from commit messages. When PRs are the source of truth, use PR labels (e.g., `type:feature`, `type:fix`, `type:breaking`) for grouping. Prefer PR metadata over raw commits when squash merges flatten history.

3. **Draft changelog sections.** Use impact-focused language: describe what changed and why it matters to users, not implementation details. Group entries under standard headers: Added, Changed, Fixed, Deprecated, Removed, Security, Breaking Changes.

4. **Handle breaking changes.** Every breaking change must appear under a dedicated "Breaking Changes" section with a clear migration note: what was removed or changed, what to do instead, and any required code updates.

5. **Apply semantic version bumping rules.** Map change types to version bumps: breaking -> major; new features -> minor; fixes and patches -> patch. Validate that the proposed version matches the collected change set.

6. **Run verification.** Ensure no duplicate entries, no empty sections, correct date and version formatting, and that all referenced PRs/commits exist. Flag any entries that look auto-generated but lack human review.

## Commit Message and PR Label Conventions

**Conventional Commits (for commit-based changelogs):**
- `feat(scope): description` -> Added
- `fix(scope): description` -> Fixed
- `docs(scope): description` -> Documentation
- `refactor(scope): description` -> Changed
- `perf(scope): description` -> Performance
- `chore(scope): description` -> omit or Chore
- Footer: `BREAKING CHANGE: description` -> Breaking Changes

**PR labels (for PR-based changelogs):**
- `changelog:added`, `type:feature` -> Added
- `changelog:fixed`, `type:bugfix` -> Fixed
- `changelog:changed`, `type:refactor` -> Changed
- `changelog:breaking`, `type:breaking` -> Breaking Changes
- `changelog:skip` -> exclude from changelog

Standardize on one scheme per repo and document it in CONTRIBUTING.md.

## Output Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Short, user-facing description of the change. (#PR or commit hash)

### Changed
- Description of behavioral or API changes.

### Fixed
- Bug fix description with impact.

### Deprecated
- What is deprecated and when it will be removed.

### Removed
- What was removed and why.

### Security
- Security-related changes.

### Breaking Changes
- **Component/API name:** What broke. Migration: what to do instead. (#PR)

### Migration Notes
- Step-by-step upgrade instructions if non-trivial.

### Contributors
- @username (contributions)
```

Include contributor attribution from PR authors or commit authors when available. Link PR numbers and commit hashes for traceability.

## Common Pitfalls

- **Mixing human-written and auto-generated entries.** Avoid editing the same changelog section by hand and by automation; pick one source of truth. If humans add entries, ensure automation does not overwrite them or duplicate.

- **Missing breaking change callouts.** Breaking changes buried in "Changed" or omitted entirely cause upgrade surprises. Always surface them in a dedicated section with migration guidance.

- **Stale changelogs from squash merges.** Squash merges replace branch commits with a single merge commit. If changelog generation reads commits, it may miss individual PRs. Prefer PR-based collection when using squash merge.

- **Vague or implementation-heavy entries.** Entries like "Refactored X" or "Updated dependencies" are unhelpful. Write for end users: "Improved login performance by 40%" or "Upgraded React to v18 for concurrent features."

- **Inconsistent version or date format.** Stick to one format (e.g., [SemVer] - ISO date) and apply it everywhere.

## Constraints

- Do not invent changelog entries; every entry must trace to a real commit or PR.
- Do not remove or alter human-written changelog content without explicit instruction.
- Prefer conventional commits or documented PR labels; avoid ad-hoc parsing heuristics.
- Always include a verification step before publishing.
- Breaking changes must have migration notes; do not leave them unexplained.
- Keep entries concise (one to two sentences); link to PRs or docs for detail.