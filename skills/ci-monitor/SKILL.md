---
id: ci-monitor
name: CI Monitor
description: Use this skill when monitoring CI pipelines for failures, regressions, instability, flaky jobs, and ownership signals, then prioritizing fixes with clear evidence and next actions.
category: DevOps
---

# CI Monitor

Track CI health and drive rapid recovery from failing pipelines.

## When to Use

- CI pipelines are flaky, failing, or slowing down delivery.
- You need visibility into failure trends and ownership gaps.
- You want a repeatable process to improve CI reliability.

## Workflow

### 1. Collect pipeline outcomes and failure categories

- **Sub-steps:** Query CI API or logs for the last 7-14 days; extract job names, exit codes, durations, and failure messages; normalize timestamps and branch/PR context.
- **Decision criteria:** Include only main/trunk and primary release branches unless explicitly asked to analyze feature branches.
- **Techniques:** Use job-level granularity (not just pipeline-level); capture retry counts and whether failures occurred on first run vs. retry.

### 2. Identify highest-impact failing jobs and bottlenecks

- **Sub-steps:** Compute failure rate per job (failures / runs); rank by frequency x blast radius (how many PRs blocked); measure P95 duration and queue time.
- **Decision criteria:** Prioritize jobs that block merges or run on every commit. Jobs with &lt;5% failure rate may be lower priority unless they are critical path.
- **Techniques:** Cross-reference with recent code changes; flag jobs whose duration has increased &gt;20% week-over-week.

### 3. Group issues into flaky tests, infra issues, and config regressions

- **Sub-steps:** Inspect failure messages and stack traces; check for timeouts, OOM, network errors, or assertion mismatches; correlate with deployment or config changes.
- **Classification examples:**
  - **Flaky tests:** Same test passes on retry; intermittent timeouts; race conditions; environment-dependent assertions (e.g., ordering, timestamps).
  - **Infra issues:** Agent/runner failures; disk space; network timeouts; resource exhaustion; upstream service unavailability.
  - **Config regressions:** Dependency version bumps; env var changes; new required checks; permission or secret rotation.
- **Decision criteria:** If failure message mentions "timeout," "OOM," or "connection refused," lean toward infra. If failure correlates with a specific commit touching config or deps, lean toward config regression.

### 4. Assign remediation owners and due dates

- **Sub-steps:** Map jobs to owning teams via CODEOWNERS, package paths, or historical ownership; set SLO-based due dates (e.g., P0: 24h, P1: 3 days, P2: 1 week).
- **Decision criteria:** Unassigned jobs go to platform/DevOps by default. Flaky tests typically owned by the team that maintains the test; infra by platform.
- **Techniques:** Include a single owner per issue; avoid "TBD" without a fallback escalation path.

### 5. Verify improvements with trend comparison

- **Sub-steps:** Re-run the same metrics after remediation window; compare success rate, mean duration, and flake recurrence; document before/after.
- **Decision criteria:** Consider a fix verified if failure rate drops by at least 50% or below 2% for that job, and no new regressions appear.
- **Techniques:** Use the same time window (e.g., 7 days) for before/after to avoid seasonal bias.

## Common Pitfalls

1. **Treating all failures equally:** Do not prioritize rare, one-off failures over recurring flaky tests that block dozens of PRs daily.
2. **Ignoring retries:** Jobs that pass on retry still indicate instability; count them as failures or track retry rate separately.
3. **Over-attributing to "flakiness":** Timeouts and OOM often point to infra or resource limits, not test logic. Misclassification delays real fixes.
4. **No ownership:** Leaving issues unassigned or assigning to generic channels ensures they will not be fixed. Always name a specific owner or escalation path.
5. **Skipping verification:** Declaring a fix complete without re-measuring leads to false confidence and recurring issues.

## Output Format

```markdown
## CI Health Snapshot
- **Success rate:** <percent> (target: >=95% for main branch)
- **Mean pipeline duration:** <time> (target: no &gt;15% increase WoW)
- **P95 queue time:** <time> (target: &lt;10 min for standard runners)
- **Top 5 failing jobs:** <name> - <failure_rate>% - <runs_in_period>
- **Flake rate:** <percent> (pass-on-retry / total runs)

## Failure Categories (last 7 days)
| Category        | Count | Example jobs                    |
|-----------------|-------|---------------------------------|
| Flaky tests     | N     | unit-integration, e2e-auth      |
| Infra          | N     | build-cache, deploy-staging     |
| Config         | N     | lint-deps, security-scan         |

## Priority Fixes
| # | Issue | Category | Owner | Due | Blast radius |
|---|-------|----------|-------|-----|--------------|
| 1 | <job> | <cat>   | <team>| <date> | <PRs blocked> |
| 2 | ...   | ...     | ...   | ...  | ...          |

## Verification Checklist
- [ ] Success rate >=95% or improved by >=50% for targeted jobs
- [ ] Mean duration stable (+/-15% WoW)
- [ ] Queue time &lt;10 min P95
- [ ] Flake recurrence tracked and &lt;2% for critical path jobs
- [ ] No new P0/P1 regressions in verification window
```