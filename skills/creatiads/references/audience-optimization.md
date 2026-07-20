# Audience Optimization

Use this reference for targeting, audience quality, placement/device/geography mix, audience fatigue, and cheap-click diagnosis.

## Required Scope

Resolve:

- platform and account scope
- date range and comparison range
- user type and confidence
- metric preset and active core metrics

Use explicit breakdowns before generic commentary.

## Required Lenses

| Lens | Expected evidence |
| --- | --- |
| Country or geo | Spend share, result share, CPA/CVR, value when active |
| Age and gender | Segment efficiency and weak-CVR segments |
| Placement | Placement spend concentration, CTR, result quality |
| Device/platform | Device quality and app/web path fit |

For TikTok, use audience-compatible report routes when required. If a combination fails, split into narrower dimensions and mark the rejected combination as `unsupported`.

## Segment Tags

- `scale`: meaningful spend share and better-than-average result quality.
- `monitor`: meaningful spend share and near-average result quality.
- `reduce`: high spend share and materially worse cost or quality.
- `weak_cvr`: conversion rate materially below average.
- `cheap_click_trap`: high CTR or cheap CPC with weak result quality.
- `no_result_spend`: non-trivial spend with zero result.
- `neutral`: no strong signal.

## Diagnosis Rules

| Signal | Likely issue | Next step |
| --- | --- | --- |
| Frequency rises while CTR falls | audience fatigue or narrow delivery | refresh creative, expand or split audience |
| CPM rises and CTR falls | creative-audience mismatch or auction pressure | creative analysis before budget increase |
| Low CPM, high clicks, weak result | low-intent traffic | inspect placement, device, landing/app path |
| One placement spends heavily with weak result | placement mismatch | compare placement-level CPA and creative format |
| Strong clicks, weak app/store event | W2A or store mismatch | run landing/app path analysis |
| High result, weak deeper event | optimization too shallow | recommend deeper event after evidence |

## Output

Return:

- supported and unsupported breakdowns
- scale candidates
- top problem segments
- cheap-click traps
- measurement warnings
- approval-gated changes only as recommendations, not executed actions
