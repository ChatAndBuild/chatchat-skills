---
id: gitlab-ci-patterns
name: GitLab CI Patterns
description: Use this skill when applying reliable GitLab CI pipeline patterns for faster feedback, safer deploys, maintainable configuration, caching, stages, rules, and runner behavior.
category: DevOps
---

# GitLab CI Patterns

Use proven GitLab CI patterns to improve speed, stability, and clarity.

## When to Use

- You need to design or refactor `.gitlab-ci.yml` workflows.
- You want clearer stage boundaries and safer deploy gates.
- You need to reduce flaky or slow jobs.

## Workflow

1. **Define pipeline stages and expected outputs.** Map stages to your delivery flow (build, test, deploy) and ensure each job has a clear, verifiable output.

2. **Use `rules` instead of `only`/`except`.** Prefer `rules` for conditional execution; `only`/`except` are deprecated. Example:

```yaml
test:
  script: [npm test]
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

3. **Build a DAG with `needs`.** Skip unnecessary stage waits by declaring job dependencies. Jobs with `needs` run as soon as their dependencies complete, not when the whole stage finishes:

```yaml
deploy-staging:
  needs: [unit-test, integration-test]
  stage: deploy
  script: [./deploy.sh staging]
```

4. **Use `includes` and `extends` for reuse.** Extract shared config into templates and compose pipelines from them:

```yaml
include:
  - local: '/templates/test-base.yml'
  - project: 'my-group/ci-templates'
    file: '/deploy.yml'

.deploy_template:
  extends: .base_job
  script:
    - ./deploy.sh $ENVIRONMENT
```

5. **Split large pipelines with parent-child pipelines.** Use `trigger` to spawn child pipelines for monorepos or parallel workflows:

```yaml
trigger-matrix:
  stage: test
  trigger:
    include: ci/child-pipeline.yml
    strategy: depend
```

6. **Add caching and artifact strategy.** Use cache keys that include branch, lockfile hash, or job name to avoid stale caches. Set `interruptible: true` on non-critical jobs so pipelines can be cancelled when a new commit is pushed.

7. **Configure deploy jobs with approval and environment gates.** Use `when: manual` sparingly; prefer `environment` with approval rules or protected environments for production.

8. **Document failure triage and retry policy.** Specify `retry` for flaky jobs, use `allow_failure` only when the job is informational, and add clear failure messages.

## Common Pitfalls

- **Overusing `when: manual`.** Manual gates create bottlenecks. Use them only for true approval points (e.g., production deploy); automate everything else.

- **Ignoring `needs` for DAG.** Without `needs`, jobs wait for the entire stage. Declare dependencies so fast jobs (e.g., lint) don't block on slow ones (e.g., e2e).

- **Cache key mistakes.** Generic keys like `cache-key` cause cross-branch contamination. Use `$CI_COMMIT_REF_SLUG`, `$CI_JOB_NAME`, or lockfile hashes.

- **Not using `interruptible`.** Long-running jobs on outdated commits waste resources. Add `interruptible: true` to non-essential jobs.

- **Mixing `rules` with `only`/`except`.** They don't combine predictably. Use `rules` exclusively.

- **Not setting `strategy: depend` for child pipelines.** Without it, the parent can succeed even when a child fails. Set `strategy: depend` so the parent fails if a child fails.

## Output Format

```markdown
## Pipeline Structure
- Stages: <ordered list with rationale>
- Critical jobs: <list with dependencies and estimated duration>
- DAG diagram: <text description of needs relationships>

## Configuration Patterns
- Rules: <key rules and when each job runs>
- Includes/extends: <template structure and reuse>
- Parent-child: <if applicable, trigger strategy>

## Performance Optimizations
- Cache strategy: <key formula, invalidation rules, shared vs per-job>
- Parallelization: <needs-based DAG, parallel matrix jobs>
- Interruptible: <which jobs, rationale>

## Safety Gates
- [ ] Required tests pass (with retry policy)
- [ ] Approval checks pass (manual vs protected env)
- [ ] Environment checks pass
- [ ] Rollback path documented

## Example Snippet
<relevant .gitlab-ci.yml excerpt>
```

## Constraints

- Prefer `rules` over `only`/`except`; do not mix them.
- Use `needs` to form a DAG and reduce pipeline duration.
- Add `interruptible: true` to non-critical jobs.
- Cache keys must be specific (branch, lockfile, or job name).
- Use `includes`/`extends` for shared config; avoid duplication.
- Keep manual gates minimal; automate where possible.
- Document retry and failure-handling behavior for each job.