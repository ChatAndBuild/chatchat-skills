---
id: update-release-notes
name: Update Release Notes
description: Use this skill when release notes must explain what changed, who is affected, what readers should do next, and any user-facing impact, migration concern, rollout caveat, or risk area.
category: Tools
---

# Update Release Notes

Use this skill when the user needs release notes that explain what changed, who is affected, and what readers should actually do next.

## Clarify First
- Who the release notes are for: users, admins, developers, or internal teams.
- Which changes are user-visible versus internal only.
- Whether there are migrations, deprecations, or rollout caveats.
- What risks, limitations, or known issues should be surfaced.
- Whether the notes should summarize one release, a hotfix, or a larger train of changes.

## Release Note Priorities
- Focus on impact, not raw commit inventory.
- Group changes in a way the reader can quickly scan.
- Call out required actions, compatibility concerns, and known limitations.
- Be honest about risk and incomplete rollout details.
- Keep language specific enough to be useful without turning into an internal diff dump.

## What Good Release Notes Include
- Clear summary of notable changes.
- Reader-relevant categories such as features, fixes, breaking changes, and operational notes.
- Upgrade or migration guidance where needed.
- Known issues or rollout caveats when they matter.
- Audience-appropriate level of technical detail.

## Common Mistakes
- Repeating commit messages instead of explaining user impact.
- Hiding breaking or risky changes in minor bullet points.
- Mixing internal implementation detail with no reader benefit.
- Omitting upgrade steps because they feel inconvenient.
- Writing notes so vague that users cannot tell whether they are affected.

## Good Output
- Release summary tailored to the audience.
- Well-grouped bullet points by change type or impact.
- Explicit upgrade, migration, or rollback notes where applicable.
- Known issues or cautionary notes when relevant.

## Boundaries
- Do not imply a feature is fully rolled out or stable unless the user confirms that status.
- Prefer clear impact-focused writing over changelog noise or marketing filler.
