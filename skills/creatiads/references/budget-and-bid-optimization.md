# Budget And Bid Optimization

Use this reference when the user asks what to scale, maintain, fix, reduce, pause, or how to interpret bid and budget behavior.

## Safety

- Never execute budget, bid, status, duplicate, share, create, or activate operations without explicit approval.
- Present the exact target IDs, intended fields, expected effect, and risks before any write.
- Do not scale based on one-day data unless the user is managing an urgent incident.
- Do not use sampled or degraded sources for final budget decisions without saying so.

## Required Evidence

- Spend, result, value, and cost by campaign and ad group.
- Objective, optimization goal, billing event, bid strategy, and budget when available.
- Trend vs comparison window.
- Vertical-specific quality metric.
- Blocking errors, review status, account balance, and delivery status when diagnosing spend drops.

## Action Bands

| Band | Evidence | Recommendation |
| --- | --- | --- |
| `scale` | Stable spend, efficient cost, healthy vertical metric | Increase 10-20% or duplicate/test after approval |
| `maintain` | Efficient but limited evidence or learning risk | Keep budget and monitor |
| `fix` | Spend with mixed evidence | Refresh creative, adjust audience/placement/bid, or fix landing |
| `reduce` | Inefficient with enough spend | Reduce 10-30% after approval |
| `pause` | High spend, no result, no assist signal | Pause only after approval |
| `measurement_risk` | Cost looks good but deeper/value metric missing | Do not scale until metric quality is clarified |

## Bid Diagnosis

| Symptom | Interpretation |
| --- | --- |
| Low delivery with tight bid/cost cap | bid too restrictive or audience too narrow |
| Spend spike and CPA worsens | broad delivery without quality guardrail |
| High CPM and low CTR | creative or audience quality before bid issue |
| Good CPA and weak downstream value | optimize toward deeper event |
| Delivery stops while objects are enabled | budget, billing, review, schedule, or platform limit |

## Output

Return a budget move table:

| Entity | Current spend | KPI | Diagnosis | Recommendation | Approval needed |
| --- | ---: | --- | --- | --- | --- |

Every mutation remains a plan until the user approves it.
