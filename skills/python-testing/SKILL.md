---
id: python-testing
name: Python Testing
description: Use this skill when designing Python tests that are clear, maintainable, and sensitive to Python-specific failure patterns such as fixtures, parametrization, side effects, exceptions, and stateful runtime behavior.
category: Testing & Security
---

# Python Testing

Use this skill to design Python tests that are clear, maintainable, and sensitive to Python-specific failure patterns.

## Clarify First
- What is under test and what external state it touches.
- Which exceptions, side effects, or mutable state transitions matter.
- Whether fixtures, parametrization, or patching are helping or hiding problems.
- What behavior should remain explicit even if helper abstractions exist.

## Python Testing Priorities
- Make fixtures serve readability, not hide setup complexity.
- Use parametrization where it clarifies input variation.
- Be explicit about exceptions, warnings, and failure semantics.
- Control filesystem, environment, network, and time when they affect behavior.
- Watch for mutable shared state and order-dependent tests.

## Good Output
- Scenario-based Python test plan.
- Fixture or parametrization suggestions.
- Warnings about hidden state, monkeypatching, or brittle assertions.
- Missing failure or edge cases worth covering.

## Common Mistakes
- Fixtures that hide more than they help.
- Overusing patching so the test stops reflecting real behavior.
- Missing assertions around exceptions or warnings.
- State leakage between tests through globals, caches, or mutable defaults.
