# Measurement And Attribution

Use this reference for metric mismatch, missing revenue, attribution-window questions, SKAN/SAN limitations, modeled data, and app/web path conflicts.

## Common Causes

| Cause | Platforms |
| --- | --- |
| Attribution window differences | TikTok |
| Impression-time vs conversion-time reporting | TikTok |
| SKAN privacy thresholds and delayed postbacks | TikTok |
| SAN availability by campaign or app configuration | TikTok |
| Mixed optimization goals inside aggregated reports | TikTok |
| W2A redirects losing web context | TikTok |
| Unsupported or gated metric groups | TikTok |

## Checks

TikTok:

- campaign dedicated type or app/SAN route
- SKAN metrics and postback sequence
- SAN/app event metrics
- result/cost-per-result mismatch when ad groups have mixed goals
- metrics returning empty, dash, or invalid under a level/product combination

## Metric States

- `decision_grade`: populated, compatible with the level, and aligned with business goal.
- `directional`: useful but affected by attribution, modeling, SKAN delay, or proxy status.
- `supported_empty`: accepted by the API but empty in this window.
- `unsupported`: rejected or unavailable for this account, product, level, or permission.
- `not_queried`: skipped by depth, request budget, or unavailable MCP route.

Unsupported does not mean the business event never happens. Supported-empty does not prove the event is absent outside the selected date range.

## W2A Rules

For tracker or self-domain-to-store paths:

- Web landing metrics may measure clicks without final app conversion.
- App install, trial, subscribe, registration, SKAN, or SAN metrics may be more relevant than web purchase.
- If only store redirect evidence exists and app events are empty, report a measurement gap.

## Output

Return:

- what differs
- likely reporting or attribution explanation
- decision-grade metrics
- directional metrics
- unavailable metrics
- next probe or configuration step
