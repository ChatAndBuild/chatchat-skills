---
id: parallel-feature-development
name: Parallel Feature Development
description: Use this skill when coordinating multiple concurrent features, stacked PRs, branch strategy, dependency sequencing, integration checkpoints, feature flags, or release timing without destabilizing main.
category: Development
---

# Parallel Feature Development

Run several feature tracks in parallel while keeping delivery predictable and integration risk low.

## When to Use

- Multiple developers are shipping related features at the same time.
- Shared files or APIs create frequent merge conflicts.
- You need a repeatable process for syncing, testing, and integrating feature branches.

## Workflow

1. **Define feature tracks and owners, then map dependencies between tracks.** Assign a single owner per track. Document which tracks depend on others (e.g., Feature B needs API changes from Feature A). Use a dependency graph or table; avoid implicit assumptions.

2. **Choose a branch model and document merge direction.** Options: (a) **Feature flags + trunk-based:** all work merges to `main` behind flags; partial integration happens in production. (b) **Integration branch:** feature branches merge to an `integration/xyz` branch for combined testing before merging to `main`. (c) **Stacked PRs:** small PRs stack on each other; each merges to `main` in sequence. Document which branches flow where and who merges when.

3. **Identify shared touchpoints and conflict hotspots.** List schemas, APIs, config files, and shared UI components. Use `git log` or conflict history to find files that change often across features-these are hotspots. Assign owners or split files to reduce contention.

4. **Add integration checkpoints.** Require daily (or twice-daily) rebase/merge from the base branch. Run smoke tests or a minimal integration suite after each sync. Catch conflicts early; do not defer integration until merge day.

5. **Merge in dependency order and run final validation.** Merge tracks that others depend on first. Run full end-to-end tests before release. Have a rollback plan for each track.

## Decision Criteria: Integration Branch vs Feature Flags vs Stacked PRs

| Approach | Best when | Trade-offs |
|----------|-----------|------------|
| **Feature flags** | Features can ship partially, teams want continuous delivery, low risk of breaking main | Requires flag infrastructure; flags can accumulate if not cleaned up |
| **Integration branch** | Features must be tested together before main, release cadence is batch-oriented | Merge debt; integration branch can drift from main; extra merge at the end |
| **Stacked PRs** | Small, incremental changes; each PR is independently shippable | Requires discipline; base PRs must merge first; can block if reviews are slow |

Choose feature flags when you can ship incrementally and want to avoid long-lived branches. Choose integration branches when you need combined testing before main. Choose stacked PRs when changes are small and sequential.

## Common Pitfalls

- **Long-lived branches causing merge debt.** Branches that live for weeks accumulate large merges and conflicts. Prefer short-lived branches, feature flags, or stacked PRs to keep branches small.
- **Skipping integration checkpoints.** Teams skip daily syncs when "things look fine," then hit big conflicts at merge time. Enforce checkpoints; treat them as non-negotiable.
- **Implicit dependencies between feature tracks.** Developers assume "Feature B will be ready" without documenting or sequencing. Make dependencies explicit and merge in order.
- **Code freeze as a crutch.** Freezing main before release hides integration problems instead of fixing them. Prefer continuous integration and feature flags so main stays stable.

## Output Format

```markdown
## Parallel Feature Plan
- Base branch: <branch>
- Branch model: <feature flags + trunk | integration branch | stacked PRs>
- Feature tracks:
  - <feature A> | owner: <name> | depends on: <none|A|B> | target merge: <date>
  - <feature B> | owner: <name> | depends on: <none|A|B> | target merge: <date>

## Shared Touchpoints and Conflict Hotspots
- Schemas/APIs: <paths, owners>
- Config: <paths, owners>
- Shared UI: <paths, owners>
- High-conflict files (from history): <paths, mitigation>

## Integration Checkpoints
- Sync cadence: <daily | twice daily>
- Sync action: <rebase | merge> from <base branch>
- Required checks after sync: <unit, integration, smoke, e2e>
- Escalation: <who to notify if sync fails>

## Merge Order and Validation
1. <branch> (rationale: no deps)
2. <branch> (rationale: depends on 1)
3. <branch>
- Final validation: <e2e suite, manual checks>
- Rollback plan: <per-track rollback steps>

## Risks and Mitigations
- <risk> -> <mitigation>

## Readiness Checklist
- [ ] Owners assigned for each feature track
- [ ] Dependencies between tracks explicit and agreed
- [ ] Shared touchpoints and hotspots documented with owners
- [ ] Branch model chosen with rationale
- [ ] Sync cadence and required checks agreed
- [ ] Merge order and rollback plan confirmed
```

## Constraints

- Keep branch lifetimes short; long-lived branches increase conflict cost.
- Do not skip integration checkpoints, even when features look independent.
- Require explicit ownership for shared modules to avoid conflicting edits.
- Make dependencies between tracks explicit; never assume ordering.
- Avoid code freeze as primary integration strategy; prefer continuous integration.