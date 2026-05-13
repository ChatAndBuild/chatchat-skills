---
id: property-based-testing
name: Property Based Testing
description: Use this skill when designing tests around invariants, generated inputs, shrinking, edge-case discovery, and regression checks instead of hand-picking every case one by one.
category: Testing & Security
---

# Property Based Testing

Use this skill to design tests around invariants, generated inputs, and edge-case discovery rather than hand-picking every case one by one.

## When It Fits Best
- The behavior should always or never hold.
- The code accepts many valid inputs or combinations.
- Edge cases are hard to enumerate manually.
- Example tests already exist, but they are not enough to challenge the implementation.

## Start By Clarifying
- What the unit under test guarantees.
- Which inputs are valid, invalid, or constrained by business rules.
- What would count as a real failure versus an irrelevant oddity.
- Whether the code depends on time, randomness, ordering, or async behavior.

## Good Property Design
- Test stable invariants, not implementation details.
- Combine property-based tests with example-based tests.
- Prefer properties that explain behavior clearly enough for future readers.
- Use generated data to challenge the code, not to rewrite the production algorithm inside the test.

## Common Property Patterns
- Output always satisfies a validity condition.
- Transformations preserve key structure or meaning.
- Two implementations agree on the same input.
- Doing an operation and then its inverse gets back to the original result.
- Reordering or combining inputs preserves a known property.

## Failure Prevention
- Control unstable inputs like time, randomness, locale, and async scheduling when they would make failures noisy.
- Keep generators as broad as the real requirements allow.
- Avoid over-constraining inputs just to make tests pass more easily.
- Treat shrinking and reproducibility as part of the debugging workflow.

## Good Output
- Candidate properties worth testing.
- Suggested input strategy and constraints.
- Warnings about unstable dependencies or false confidence.
- A balanced test plan that mixes properties with concrete examples.

## Common Mistakes
- Using property tests where a few examples would explain the behavior better.
- Writing properties so vague they pass without testing much.
- Filtering generated inputs heavily instead of modeling valid inputs directly.
- Confusing exhaustive testing with property-based testing.
