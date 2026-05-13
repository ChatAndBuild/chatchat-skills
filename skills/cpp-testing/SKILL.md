---
id: cpp-testing
name: C++ Testing
description: Use this skill when designing C++ tests where memory ownership, lifetime, undefined behavior, boundary conditions, concurrency, isolation seams, or deterministic behavior matter.
category: Testing & Security
---

# C++ Testing

Use this skill to design tests for C++ code where memory ownership, lifetime, undefined behavior, and boundary conditions matter.

## Clarify First
- What level is under test: function, class, module, or integration seam.
- Which ownership and lifetime assumptions the code relies on.
- Whether concurrency, exceptions, or resource cleanup are involved.
- Which inputs or states are most likely to trigger subtle bugs.

## C++ Testing Priorities
- Cover boundary conditions and invalid states deliberately.
- Make ownership and resource expectations visible in the tests.
- Prefer seams that isolate behavior without hiding lifetime issues.
- Treat nondeterminism, time, and thread scheduling carefully.
- Use tests to expose invariants around construction, mutation, and cleanup.

## Good Output
- A scenario-based C++ test plan.
- Edge cases around ownership, cleanup, and invalid state.
- Suggestions for making code more testable without obscuring correctness risks.
- Warnings about brittle or UB-sensitive test approaches.

## Common Mistakes
- Ignoring object lifetime and cleanup behavior.
- Testing only happy-path values in code with risky ownership semantics.
- Mocking away the exact resource behavior that matters.
- Letting undefined behavior slip through because the test passed once.
