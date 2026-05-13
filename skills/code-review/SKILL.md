---
id: code-review
name: Code Review
description: Use this skill when reviewing a code change for correctness, behavioral risk, maintainability, unclear contracts, missing verification, and findings-first feedback rather than style polish.
category: Tools
---

# Code Review

Use this skill when the user wants help reviewing a code change for correctness, risk, maintainability, and missing verification rather than just style polish.

## Start By Clarifying
- What changed and why.
- Which behavior is user-facing, stateful, or high-risk.
- What assumptions the change makes about inputs, data flow, or external systems.
- Which tests or verification steps already exist.
- Whether the review should emphasize bugs, regressions, architecture, or readability.

## Review Priorities
- Behavioral correctness and regression risk.
- Contract changes and hidden coupling.
- Error handling, edge cases, and state transitions.
- Clarity of abstractions and maintainability.
- Adequacy of tests relative to the risk of the change.

## What A Good Review Should Surface
- Findings ordered by severity.
- Why each issue matters in runtime or maintenance terms.
- Missing tests where uncertainty remains high.
- Places where the code is harder to reason about than it needs to be.
- Explicit distinction between bugs, risks, and optional cleanup.

## Common Mistakes
- Focusing on naming and formatting while missing behavior changes.
- Approving code that works only under happy-path assumptions.
- Ignoring hidden contract changes because the types still compile.
- Treating missing tests as optional even when the change is risky.
- Giving generic feedback instead of tying comments to concrete impact.

## Good Output
- Findings-first review summary.
- Open questions or assumptions that affect confidence.
- Test gaps or verification concerns.
- Secondary cleanup suggestions only after the important issues.

## Boundaries
- Do not claim a change is safe just because it looks clean or compiles.
- Prefer bug finding, risk framing, and test scrutiny over generic style commentary.
