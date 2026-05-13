---
id: javascript-testing-patterns
name: JavaScript Testing Patterns
description: Use this skill when JavaScript-specific runtime behavior makes generic test advice too shallow, including async behavior, timers, modules, mocks, browser-like environments, and stateful edge cases.
category: Testing & Security
---

# JavaScript Testing Patterns

Use this skill when JavaScript-specific behavior makes generic unit-test advice too shallow.

## Focus Areas
- Async flows, promises, retries, and race conditions.
- Timers, scheduling, and event-loop behavior.
- Module boundaries, imports, and side effects.
- Browser-like globals, DOM-adjacent behavior, or runtime assumptions.
- Mocking choices and how they affect trust in the test.

## Useful Patterns
- Control time explicitly when timers or retries matter.
- Test observable behavior of async code, not incidental ordering details.
- Isolate side effects at module boundaries.
- Be cautious with mocks that rewrite too much of the runtime contract.
- Prefer patterns that keep tests readable under refactoring.

## Good Output
- JavaScript-specific test scenarios worth adding.
- Warnings about timers, globals, mocks, or async flakiness.
- Suggestions for cleaner seams around side effects.
- Notes on what should be tested synchronously versus with async orchestration.

## Common Mistakes
- Letting fake timers or microtask behavior hide real bugs.
- Over-mocking modules until the test no longer reflects runtime behavior.
- Ignoring race conditions in code that awaits or schedules work.
- Treating DOM-like globals as harmless implicit state.
