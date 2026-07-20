# Error, Cache, And Degradation Policy

Use this reference when analysis hits authentication problems, permission failures, rate limits, unsupported metrics, empty metrics, timeouts, partial coverage, cached context, or sampled account sets.

## Coverage States

| State | Meaning |
| --- | --- |
| `full` | Explicit requested accounts completed at requested depth |
| `batch` | Explicit accounts completed with a low-request profile suitable for many accounts |
| `partial` | Some requested accounts, sources, or capability groups completed |
| `sampled` | User approved recent-spend or active-account sampling |
| `degraded` | Required source failed and conclusions are lower confidence |
| `failed_with_reason` | No usable result; include sanitized reason |

## Failure Handling

| Failure | Action |
| --- | --- |
| Missing account IDs | Ask for account or advertiser scope |
| User type missing with account IDs present | Run classification and record source |
| Classification failed | Continue with universal core metrics and mark vertical sections unavailable |
| Permission error | Report missing permission/resource and stop that source |
| Rate limit | Reduce page size, depth, or breakdowns; mark skipped source |
| Unsupported metric group | Split requests or mark unsupported |
| Timeout | Preserve baseline sources and mark deep sections partial |
| Empty response | Distinguish no data from permission or query failure |
| MCP namespace unavailable | Return structured unavailable; do not fall back to a non-MCP source |

## Metric States

| State | Meaning |
| --- | --- |
| `active` | Returned non-zero/non-empty evidence |
| `supported_empty` | Accepted but zero/empty in selected window |
| `unsupported` | Rejected or unavailable in context |
| `invalid_combination` | Metric and dimension cannot be requested together |
| `not_queried` | Skipped by depth or request budget |

## Cache Guidance

Cached or prior-run context may be reused for:

- account metadata
- user type classification
- landing/app/W2A evidence
- metric support maps
- recent capability summaries

Rules:

- State when evidence is cached or prior-run.
- Do not use cached data as current performance fact.
- Refresh daily/weekly KPI sources for the requested window.
- Re-run classification if cached user type conflicts with fresh landing/app evidence.

## Degradation Notice

When returning partial output, include:

```text
Coverage state: full | batch | partial | sampled | degraded | failed_with_reason
Completed: ...
Skipped: ...
Reason: ...
Recommended follow-up: ...
```
