---
id: e2e-testing-patterns
name: E2E Testing Patterns
description: Use this skill when building or refactoring end-to-end test suites that cover critical user journeys with stable selectors, controlled test data, reliable waits, and clear failure triage.
category: DevOps
---

# E2E Testing Patterns

Create E2E suites that detect real regressions without becoming flaky or slow.

## When to Use

- You are defining E2E coverage for core user flows.
- Existing tests are flaky, slow, or hard to debug.
- You need consistent patterns for selectors, fixtures, and retries.

## Concrete Framework Patterns

**Playwright:** Use `page.getByRole()`, `page.getByLabel()`, `page.getByTestId()` for resilient selectors. Prefer `data-testid` for complex widgets. Use `page.waitForLoadState('networkidle')` or `page.waitForResponse()` for async flows. Enable traces: `trace: 'on-first-retry'` for failure diagnosis.

**Cypress:** Prefer `cy.get('[data-cy=...]')` or `cy.findByRole()`. Use `cy.intercept()` to stub APIs and assert on requests. Use `cy.wait('@alias')` for explicit network waits. Enable video and screenshots on failure.

**WebdriverIO:** Use `$('[data-testid=...]')` or custom strategies. Leverage `waitForDisplayed()` and `waitForExist()` with timeouts. Use `browser.pause()` only for local debugging; replace with explicit waits before commit.

**Selector strategies:** Prefer semantic (role, label, placeholder) over CSS classes or XPath. Reserve `data-testid` for elements without semantic hooks. Avoid selectors that depend on DOM order, dynamic IDs, or visual layout.

## Test Architecture Guidance

**Page object model:** Encapsulate selectors and actions per page/screen. Expose methods like `login(email, password)` and `submitOrder()`. Tests call page objects; selectors live in one place.

**Fixture factories:** Create factories (e.g., `createUser()`, `createOrder()`) that return API-seeded data. Use unique identifiers (UUIDs, timestamps) to avoid collisions in parallel runs.

**API-seeded state:** Seed users, products, and orders via API or DB before tests. Do not rely on UI flows to create prerequisite data when API is faster and more reliable.

## CI Optimization

**Parallelism with sharding:** Split suite by file or tag; run shards in parallel. Use `--shard=1/4` (Playwright) or Cypress `--parallel` to reduce wall-clock time.

**Video/trace capture:** Capture on first retry or failure only to save storage. Use `trace: 'on-first-retry'` (Playwright) or `video: true` with retention limits.

**Retry budgets:** Allow 1-2 retries for known-flaky tests while fixing root cause. Do not use high retries to mask deterministic bugs; treat flaky tests as defects.

## Common Pitfalls

- **Testing through the UI what should be API-tested:** Setup, teardown, and data validation belong in API/unit tests. E2E should focus on user-visible flows.
- **Shared mutable test accounts:** Shared accounts cause collisions and order-dependent failures. Use unique accounts per test or per worker.
- **Arbitrary sleeps instead of explicit waits:** `sleep(3000)` hides timing issues and slows suites. Use `waitForSelector`, `waitForResponse`, or framework-specific wait utilities.
- **Screenshot-only failure evidence:** Screenshots help but are insufficient. Include trace files (Playwright), console logs, network logs, and the failing assertion context.

## Workflow

1. Identify tier-1 journeys (revenue, auth, onboarding, critical CRUD).
2. Define scenarios per journey: happy path, validation/error states, permission/role differences where relevant.
3. Use stable selectors (`data-testid` or semantic roles), not visual CSS paths.
4. Control test state: seed fixtures via API or DB setup; avoid dependence on shared mutable accounts.
5. Add explicit waits for domain events (network response, URL state, visible text), not arbitrary sleeps.
6. Group tests by feature; keep each test independent and restartable.
7. Add failure artifacts: screenshots, traces, console/network logs.

## Reliability Checklist

- [ ] Selectors are resilient to UI layout changes.
- [ ] Tests can run in parallel without data collisions.
- [ ] Retries are limited and not masking deterministic bugs.
- [ ] Failures include enough context for first-pass diagnosis (trace, logs, assertion).

## Output Format

Return:

- **Coverage map by user journey:** Journey name, scenarios, priority.
- **Test case list:** Name, preconditions, steps, assertions.
- **Selector strategy:** Framework, preferred selectors, `data-testid` conventions.
- **Flakiness risks and mitigation:** Known flaky areas, wait strategy, isolation approach.
- **CI strategy:** Parallelism (shards), retries, artifacts (video/trace), retention.

```markdown
## E2E Plan
### Coverage Map
| Journey | Scenarios | Priority |
|---------|-----------|----------|
| ...     | ...       | ...      |

### Test Cases
| Name | Preconditions | Assertions |
|------|---------------|------------|
| ...  | ...           | ...        |

### CI Configuration
- Shards: <count>
- Retries: <count>
- Artifacts: video on failure, trace on retry
```

## Constraints

- Do not over-test every permutation at E2E level; keep scope to critical paths.
- Avoid coupling tests to implementation details.
- Treat flaky tests as defects to fix, not tests to ignore.
- Prefer API for setup/teardown; reserve E2E for user-visible flows.