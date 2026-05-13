---
id: subagent-driven-development
name: Subagent-driven Development
description: Use this skill when decomposing and coordinating multi-step implementation or DevOps work across focused subagents with explicit ownership, handoffs, validation, and final integration checks.
category: Development
---

# Subagent-driven Development

Coordinate complex DevOps work by decomposing tasks into subagent workflows.

## When to Use

- You have a large delivery task with independent workstreams.
- You need faster execution through parallel analysis and implementation.
- You want consistent quality gates across separately produced outputs.

## Decomposition Techniques

**MECE task breakdown.** Split the objective into Mutually Exclusive, Collectively Exhaustive subtasks. Each subtask has a single owner (subagent), no overlap with others, and together they cover the full scope. If two subtasks could both modify the same file, refine the split (e.g., by layer, by feature flag, or by file prefix).

**Dependency graph for ordering.** Build a directed graph: Task A -> Task B means B depends on A's output. Identify the critical path and parallelizable branches. Run tasks with no dependencies first; fan-out to parallel tasks; fan-in when dependencies are satisfied. Use topological sort to determine merge order.

**Input/output contract per subagent.** For each subagent, define: (1) Inputs: files, config, or artifacts it receives. (2) Outputs: files created, config changes, or artifacts produced. (3) Success criteria: how to verify the output. (4) Side effects: what it must not touch. Write this as a short contract in the subagent prompt.

## Coordination Patterns

**Fan-out/fan-in.** One orchestrator splits work into N parallel subagent tasks. Each subagent produces an artifact. The orchestrator waits for all, then merges or reconciles. Use when tasks are independent and outputs can be combined (e.g., separate config files, different modules).

**Pipeline chain.** Task 1 -> Task 2 -> Task 3. Each task consumes the previous output. Use when there is a clear sequence (e.g., schema migration -> code update -> test update). Hand off via shared artifacts or explicit output/input declarations.

**Shared artifact repository.** All subagents read from and write to a shared location (branch, directory, or doc). Define naming conventions and merge rules upfront. Use a single reconciliation step to resolve conflicts, standardize formatting, and produce the final integrated artifact.

## Task Decomposition Examples

**CI hardening:** Task A (lint config) -> outputs `.eslintrc`, `.prettierrc`. Task B (test config) -> outputs `jest.config.js`, test scripts. Task C (pipeline YAML) -> consumes A and B outputs, produces `.github/workflows/ci.yml`. Dependencies: C depends on A and B. Run A and B in parallel; then C.

**Observability:** Task A (metrics) -> instrument app code, add Prometheus client. Task B (logging) -> add structured logger, log format. Task C (dashboards) -> create Grafana JSON. No file overlap; run in parallel. Reconciliation: ensure metric names and log fields align with dashboard queries.

**Platform migration:** Task A (database) -> migration scripts, connection config. Task B (API layer) -> update routes for new DB. Task C (frontend) -> update API calls. Dependency: B depends on A; C depends on B. Pipeline: A -> B -> C.

## Common Pitfalls

**Overlapping scope between subagents.** Two subagents editing the same file or config cause merge conflicts and inconsistent conventions. Fix by refining boundaries: assign files or modules exclusively, or have one subagent produce a spec and another implement it.

**Missing reconciliation step.** Raw subagent outputs often differ in style, naming, or assumptions. Always include a reconciliation step: a human or orchestrator reviews, resolves conflicts, and produces the final integrated artifact. Do not merge blindly.

**No integration test after merge.** Unit-validated subagent outputs can still fail when combined. Run an end-to-end or integration test on the merged result before considering the task done.

**Subagent prompts too vague.** Prompts like "improve the tests" produce inconsistent results. Use specific instructions: "Add unit tests for `UserService.create()` covering success, duplicate email, and invalid input. Use Jest. Place in `src/user/__tests__/UserService.test.ts`."

**Ignoring conflicting outputs.** When subagents produce contradictory decisions (e.g., different naming schemes, conflicting config values), document the conflict and resolve it explicitly. Do not silently pick one; record the decision for future reference.

## Workflow

1. Split the objective into bounded tasks with clear success criteria.
2. Assign each subagent a focused scope, inputs, and expected outputs.
3. Run tasks in parallel where dependencies permit.
4. Reconcile outputs, resolve conflicts, and standardize conventions.
5. Validate integrated result with tests and operational checks.

## Output Format

```markdown
## Task Decomposition
| Task | Scope | Inputs | Outputs | Success Criteria |
|------|-------|--------|---------|------------------|
| A    | <scope> | <list> | <list> | <verification> |
| B    | <scope> | <list> | <list> | <verification> |

## Dependency Graph
A --> C
B --> C
(Parallel: A, B. Sequential: C after A and B.)

## Coordination Plan
- Pattern: fan-out/fan-in | pipeline | shared repo
- Merge order: <order>
- Reconciliation: <who, what, how>
- Review gates: <checks>

## Subagent Contracts (per task)
- Task A prompt: <key instructions>
- Task A I/O: <inputs> -> <outputs>

## Completion Checklist
- [ ] Each sub-task meets acceptance criteria
- [ ] Reconciliation completed, conflicts resolved
- [ ] Integrated artifacts are consistent
- [ ] End-to-end validation passed
```

## Constraints

- Keep each subagent prompt specific and measurable.
- Do not merge conflicting outputs without reconciliation notes.
- Maintain a single source of truth for final integrated decisions.
