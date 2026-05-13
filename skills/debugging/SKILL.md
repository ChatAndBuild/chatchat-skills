---
id: debugging
name: Debugging
description: Use this skill when a systematic debugging approach is needed, using hypothesis-driven investigation, evidence gathering, reproduction quality, and safe narrowing instead of random fixes or shallow symptom chasing.
category: Tools
---

# Debugging

Use this skill when the user needs a systematic debugging approach instead of random fixes, speculative edits, or shallow symptom chasing.

## Clarify First
- What the observed symptom actually is.
- Whether the issue is reproducible, intermittent, or environment-specific.
- What changed recently around the failure.
- Which evidence already exists: logs, traces, screenshots, errors, inputs, or timing.
- What would count as proof of root cause rather than coincidence.

## Debugging Priorities
- Reproduce the problem as reliably as possible.
- Narrow the failure boundary before changing code.
- Form one strong hypothesis at a time.
- Separate observations from interpretation.
- Use the smallest safe experiment that can disprove a theory.

## Good Debugging Structure
- Symptom summary and current confidence level.
- Reproduction conditions and known variables.
- Candidate causes ordered by likelihood and blast radius.
- Next diagnostic step designed to eliminate possibilities.
- Evidence required before calling the issue understood or fixed.

## Common Mistakes
- Changing multiple things at once and losing causality.
- Confusing a correlated change with the actual cause.
- Debugging from memory instead of from current evidence.
- Treating one successful run as proof of resolution.
- Jumping to a fix before the failure boundary is clear.

## Good Output
- Structured debugging plan.
- Strongest current hypotheses and why.
- Highest-value next checks or experiments.
- Resolution criteria and regression-risk notes.

## Boundaries
- Do not pretend the root cause is known before the evidence supports it.
- Prefer disciplined narrowing and proof-oriented investigation over guess-and-check advice.
