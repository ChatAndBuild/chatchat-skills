---
id: deployment-pipeline-design
name: Deployment Pipeline Design
description: Use this skill when designing deployment pipelines with safe promotion stages, quality gates, environment consistency, rollout strategy, rollback paths, and release verification.
category: DevOps
---

# Deployment Pipeline Design

Create reliable deployment pipelines that balance release speed with operational safety.

## When to Use

- You are defining or refactoring CI/CD deployment flow.
- You need clear promotion criteria from build to production.
- You want explicit rollback and failure-handling paths.

## Workflow

### 1. Define environments, ownership, and promotion rules

- List environments in promotion order (e.g., dev -> integration -> staging -> production).
- Assign ownership per environment (who approves, who deploys, who owns incidents).
- Set promotion rules: automatic vs manual, time windows, change freezes.
- Decide which environments require parity with production (staging should mirror prod config where possible).

### 2. Add quality gates (tests, security, policy, approvals)

- **Tests**: Unit, integration, e2e; run fast tests early, slow tests before prod.
- **Security**: SAST, dependency scanning, secrets detection; fail on high/critical findings.
- **Policy**: Compliance checks, license validation, infrastructure-as-code lint.
- **Approvals**: Use for prod only when required; prefer automated gates over manual sign-off where feasible.
- Order gates by cost: cheap gates first, expensive gates last to avoid wasting resources on bad builds.

### 3. Design deployment strategy (rolling, blue/green, canary)

Choose based on service characteristics:

| Strategy | Best for | Pros | Cons |
|----------|----------|------|------|
| **Rolling** | Stateless services, low risk | Simple, no extra infra, gradual rollout | Downtime risk if bad deploy; slower rollback |
| **Blue/Green** | Stateful or high-risk services | Instant rollback, full validation before switch | 2x infra cost, DB migrations need care |
| **Canary** | High-traffic, risk-sensitive | Real traffic validation, gradual exposure | Complex routing, observability overhead |

- **Rolling**: Use when you have stateless replicas and can tolerate brief inconsistency. Set batch size and pause between batches.
- **Blue/Green**: Use when rollback must be instant or you need full prod-like validation. Plan DB migrations separately (expand-contract pattern).
- **Canary**: Use when you need to validate in production with a small subset of traffic. Define canary size (e.g., 5%), duration, and success metrics.

### 4. Define observability checks and auto-stop conditions

- Instrument health checks, latency percentiles, error rates, and business metrics.
- Set auto-stop conditions: error rate spike, latency degradation, health check failures.
- Define evaluation window (e.g., 5-minute rolling window) and thresholds.
- Ensure observability runs before and after deploy; compare baseline to post-deploy.

### 5. Document rollback playbook and post-deploy verification

- **Rollback triggers**: Manual decision, auto-stop fired, or critical alert.
- **Rollback steps**: One-command or minimal-step revert (e.g., revert to previous artifact, switch traffic back).
- **Post-deploy verification**: Smoke tests, synthetic checks, log sampling. Run within 5-10 minutes of deploy.
- **Incident handoff**: Who is paged, escalation path, when to involve on-call.

## Choosing Deployment Strategy by Service Type

- **Stateless API, low traffic**: Rolling is sufficient.
- **Stateless API, high traffic**: Canary to validate under load.
- **Stateful service, DB migrations**: Blue/green with expand-contract migrations; avoid big-bang schema changes.
- **Monolith or tightly coupled system**: Prefer blue/green for clean cutover.
- **Microservices with independent deploy**: Rolling or canary per service.

## Common Pitfalls

1. **Gating on flaky tests**: Tests that intermittently fail block all deploys. Fix or quarantine flaky tests; use retries only for known-transient failures.
2. **Manual gates as bottlenecks**: Requiring human approval for every deploy creates queues and encourages bypassing. Use automated gates; reserve manual approval for high-risk or compliance-mandated changes.
3. **Rollback depends on the person who deployed**: Rollback must be executable by anyone on-call. Document steps, automate where possible, and test rollback in staging.
4. **Deploy success tied to non-critical checks**: Failing a non-blocking check (e.g., coverage report) should not block deploy. Separate blocking vs informational gates.
5. **No observability during deploy**: Deploying without real-time metrics means you discover failures too late. Instrument before deploy; use canary or phased rollout to catch issues early.

## Output Format

```markdown
## Pipeline Stages
1. **Build**: <tool>, <artifact output>, <caching strategy>
2. **Validate**: <tests, lint, security scans>
3. **Staging Deploy**: <strategy>, <environment config>
4. **Production Deploy**: <strategy>, <approval/gate requirements>

## Environments
| Environment | Owner | Promotion | Parity with Prod |
|-------------|-------|-----------|------------------|
| dev | ... | auto | no |
| staging | ... | auto | yes |
| production | ... | manual/auto | - |

## Quality Gates (in order)
| Gate | Blocking | Failure action |
|------|----------|----------------|
| Unit tests | yes | fail pipeline |
| Integration tests | yes | fail pipeline |
| Security scan | yes (high/critical) | fail pipeline |
| E2E tests | yes | fail pipeline |
| Approval | yes (prod only) | wait |

## Deployment Strategy
- **Strategy**: <rolling|blue-green|canary>
- **Rationale**: <why this strategy for this service>
- **Parameters**: <batch size, canary %, duration, etc.>
- **Rollback trigger**: <auto-stop condition OR manual>
- **Rollback action**: <exact steps>; target under 5 min

## Observability & Auto-Stop
- **Metrics**: <list>
- **Thresholds**: <error rate, latency, health>
- **Evaluation window**: <e.g., 5 min>
- **Auto-stop action**: <pause deploy, rollback, alert>

## Rollback Playbook
1. <step>
2. <step>
3. Verification: <how to confirm rollback succeeded>
```

## Constraints

- **Prefer deterministic gates over manual ad hoc checks**: Automated gates are repeatable and scale; manual checks become bottlenecks and are skipped under pressure.
- **Keep rollback path executable within incident time targets**: If your SLO is 15-minute recovery, rollback must complete in under 15 minutes. One-command rollback is ideal.
- **Avoid coupling deployment success to non-critical checks**: Blocking on coverage, style, or informational reports slows deploys and creates false failures. Use separate reporting.
- **Never deploy without observability**: You cannot safely roll back or validate success without metrics. Instrument first.
- **Test rollback in staging**: Rollback paths that are never exercised will fail in production. Include rollback drills in release rehearsals.