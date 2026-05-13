---
id: dependency-upgrade
name: Dependency Upgrade
description: Use this skill when upgrading dependencies with risk-aware batching, compatibility checks, lockfile review, migration notes, and verification steps for routine updates or major-version changes.
category: DevOps
---

# Dependency Upgrade

Update dependencies methodically so security and compatibility improve without destabilizing delivery.

## When to Use

- Security or maintenance updates are pending.
- You are planning a major version jump with breaking changes.
- Build/test failures appear after automated dependency bumps.

## Upgrade Techniques

- **npm:** `npm outdated` for overview; `npx npm-check-updates -u` (or `ncu -u`) for targeted bumps. Use `--target minor` or `--target patch` to avoid majors. Apply in batches and run tests between batches.
- **pip:** Use `pip-compile` (from pip-tools) to regenerate `requirements.txt` from `requirements.in`. Bump packages in `.in`, then `pip-compile` to resolve. Prefer virtualenv per project.
- **cargo:** `cargo update` updates lockfile within semver; `cargo upgrade` (cargo-edit) for version bumps in `Cargo.toml`. Run `cargo test` and `cargo clippy` after each batch.
- **Renovate/Dependabot:** Configure grouping (e.g., `group:non-major` for minor/patch, separate group for majors). Use `schedule` and `assignees` to control review load. Enable automerge only for low-risk groups (e.g., devDeps, lockfile-only).

## Batching Strategy

Group by risk level:

1. **devDeps first:** Linters, test runners, build tools. Low runtime impact; fix breakages before touching runtime deps.
2. **Runtime non-breaking:** Patch and minor updates for production deps. Read changelogs for deprecations and behavior changes.
3. **Major versions last:** One major per PR when possible. Isolate in a branch; run full regression and smoke tests.

Avoid mixing framework upgrades (e.g., React) with library upgrades in the same batch; framework changes often cascade.

## Migration Planning for Major Versions

- **Codemod tools:** Use official codemods (e.g., `react-codemod`, `ember-cli-update`) or custom scripts. Run on a branch; review diffs before committing.
- **Adapter patterns:** Introduce compatibility layers for breaking APIs; migrate call sites gradually. Remove adapters once migration is complete.
- **Feature flags:** Gate new behavior behind flags for gradual rollout. Upgrade library first with backward compatibility, then flip flags and remove old paths.

## Common Pitfalls

- **Upgrading lockfile without reading changelogs:** Transitive updates can change behavior. Always check release notes for direct and critical transitive deps.
- **Peer dependency hell:** npm v7+ installs peers by default; mismatches cause install failures. Resolve with `overrides`/`resolutions` sparingly; prefer upgrading the consumer or finding compatible versions.
- **Mixing framework and library upgrades:** Upgrading React and 5 UI libraries together makes failures hard to isolate. Upgrade framework first, stabilize, then libraries.
- **Trusting green CI without smoke testing:** CI may not cover all environments or critical user paths. Run manual smoke tests on staging before production deploy.

## Workflow

1. Inventory outdated packages and classify by risk (runtime, build, dev-only).
2. Upgrade in small, reversible batches (related packages together).
3. Read changelogs/release notes for breaking changes and migration steps.
4. Apply code/config updates needed for new APIs or defaults.
5. Run full verification:
   - Unit/integration/e2e tests
   - Build/lint/typecheck
   - Focused smoke tests on critical paths
6. Record impact, unresolved warnings, and follow-up tasks.
7. Merge only when rollback path is clear and monitored.

## Validation Checklist

- [ ] Lockfile changes are intentional and reviewable.
- [ ] Peer dependency conflicts are resolved explicitly.
- [ ] Deprecated APIs are tracked with owners and deadlines.
- [ ] Performance regressions are checked for key endpoints.

## Output Format

Return:

- **Upgrade batch plan:** Ordered list of batches with rationale (risk level, dependency graph).
- **Breaking changes and required code edits:** Per-package notes and migration steps.
- **Test evidence and residual risks:** What passed, what was skipped, known warnings.
- **Recommended next upgrade batch:** What to tackle after this batch merges.
- **Rollback steps:** How to revert (e.g., `git revert`, lockfile restore) if issues appear post-merge.

## Constraints

- Avoid mixing unrelated major upgrades in one batch.
- Do not ignore warnings that indicate runtime incompatibility.
- Prefer package-manager-native upgrades over manual lockfile edits.
