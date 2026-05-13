---
id: mutation-testing
name: Mutation Testing
description: Use this skill when planning or executing mutation testing to evaluate whether a test suite catches meaningful defects, especially when coverage is high but confidence is low.
category: DevOps
---

# Mutation Testing

Use mutation testing to measure whether tests actually catch behavioral changes.

## When to Use

- Coverage metrics look good, but escaped defects still occur.
- You want to harden tests for critical business logic.
- CI needs stronger quality signals than line coverage alone.

## Concrete Tool Patterns

**JavaScript/TypeScript:** Stryker (`npx stryker run`) with `stryker.config.json`. Use `mutate` to scope files; `ignorePatterns` to exclude generated or third-party code. Mutators: arithmetic (`+`->`-`), block statement removal, conditional boundary (`<`->`<=`), string literal replacement.

**Java:** PIT (pitest) via Maven/Gradle. Scope with `targetClasses` and `targetTests`. Mutators: `CONDITIONALS_BOUNDARY`, `INCREMENTS`, `MATH`, `NEGATE_CONDITIONALS`, `VOID_METHOD_CALLS`, `REMOVE_CONDITIONALS`.

**Python:** mutmut (`mutmut run`) or cosmic-ray. Scope with `paths_to_mutate` or `--paths`. Mutators: arithmetic, comparison, logical operator replacement; constant replacement; argument removal.

**Mutation operator types:** Arithmetic (e.g., `+`->`-`), relational (`<`->`<=`), logical (`&&`->`||`), conditional boundary, statement deletion, return value replacement. Some operators (e.g., constant replacement) produce many equivalent mutants; consider excluding them if they inflate noise.

## Surviving Mutant Analysis Techniques

**Equivalent mutant detection:** Mutants that produce identical behavior are undetectable by tests. Look for mutations in dead code, constants used only for logging, or symmetric operations. Mark equivalent mutants and exclude from score calculation to avoid chasing impossible kills.

**Boundary condition mutants:** Mutations like `x < 5` -> `x <= 5` often survive when tests only hit one side of the boundary. Add explicit boundary tests (e.g., `x=4`, `x=5`, `x=6`).

**Operator replacement mutants:** Surviving arithmetic or logical mutants indicate missing assertions or edge cases. Strengthen assertions to verify computed values, not just that code ran.

## CI Integration Patterns

**Incremental mutation testing:** Run mutation only on changed files or PR-touched modules. Reduces feedback time; combine with periodic full runs.

**PR-scoped mutation:** Gate PRs on mutation score for modified files. Set threshold (e.g., 80%) with rationale; allow override for equivalent-mutant-heavy areas.

**Baseline tracking:** Store baseline scores per module; fail CI if score drops below baseline without justification.

## Common Pitfalls

- **Running on entire codebase:** Full-repo mutation is slow and produces noise. Start with critical modules; expand gradually.
- **Chasing 100% score:** Equivalent mutants make 100% impossible in many codebases. Set practical targets (e.g., 80-90%) and focus on high-risk survivors.
- **Equivalent mutants inflating kill ratio:** If you count equivalent mutants as "survived," score looks worse than it is. Track and exclude them.
- **Slow feedback loops:** Mutation is CPU-intensive. Use incremental runs, parallelization, and caching to keep feedback under 10-15 minutes where possible.

## Workflow

1. Select target scope (critical modules first, not the full codebase).
2. Configure mutation tool; exclude equivalent/noisy mutation categories where justified.
3. Run baseline mutation analysis and capture surviving mutants by file/function.
4. Analyze survivors: identify equivalent mutants, boundary gaps, weak assertions.
5. Improve tests with stronger assertions, edge cases, and state-transition checks.
6. Re-run mutation tests and set practical score thresholds for CI gates.

## Output Format

```markdown
## Mutation Testing Report
- Tool: <Stryker/pitest/mutmut/cosmic-ray>
- Scope: <paths/modules>
- Mutators enabled: <list>
- Baseline mutation score: <percent>
- Current mutation score: <percent>
- Equivalent mutants (excluded): <count>

## Surviving Mutants (Top Priorities)
| File/Function | Mutation type | Risk | Suggested fix |
|---------------|---------------|------|---------------|
| ...           | ...           | ...  | ...           |

## Test Improvements
- Added tests: <count>
- Strengthened assertions: <summary>
- Boundary tests added: <summary>
- Remaining gaps: <summary>

## CI Gate Recommendation
- Proposed threshold: <percent>
- Scope: <full/incremental/PR-scoped>
- Rationale: <short explanation>
```

## Constraints

- Start narrow; full-repo mutation runs can be prohibitively slow.
- Track equivalent mutants separately to avoid misleading score targets.
- Use mutation score as a signal, not a standalone quality metric.
- Do not chase 100%; set practical thresholds and focus on high-impact survivors.