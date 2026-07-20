# Smart+ Material Enrichment

Use this reference only as optional enrichment for Smart+ creative/ad analysis. The user-facing
benchmark has three primary grains: Campaign, Ad Group, and Ad. When the user asks which
creative/material is best, keep the main benchmark at Ad grain and use material data only to
explain what sits behind Ad-level winners or draggers. `creative_id` and material IDs can describe
the asset context, but Ad-grain object names are not linked to Ads Manager.

## Enrichment Path

1. Resolve the Campaign type and objective.
2. If `campaign_type` is `UPGRADED_SMART_PLUS`, the main path still pulls Ad-level
   `report_integrated_get` for analysis and benchmark.
3. Optionally call the Smart+ material report:
   `smart_plus_material_report_overview_run`.
4. Use the same window as the account benchmark request.
5. Use objective-aware metrics from `references/objective-metric-profiles.md`, translated through
   endpoint-specific mappings in `references/metric-catalog.md`.
6. Aggregate by `main_material_id` only for the enrichment note.
7. If the Smart+ material report is unavailable, permission-blocked, unsupported, or missing the
   needed material fields, continue with the Ad-level benchmark.

Do not present Smart+ material enrichment as a fourth benchmark grain. If material data was not
available, say the result is Ad-level creative/ad analysis only when that distinction matters.

## Aggregation Key

The enrichment unit is `main_material_id`.

Keep these fields as descriptive context:

- `main_material_name`
- `main_material_type`
- parent Campaign or Ad IDs when returned

Do not aggregate Smart+ materials by name. Names can repeat or change, while `main_material_id` is
the stable enrichment key for this report path.

## Local Aggregation

For each `main_material_id`, sum additive metrics:

- `spend`
- `impressions`
- `clicks`
- `conversion`
- `app_install`
- `form`
- `sales_lead`
- `complete_payment`
- `purchase`
- video view counts

Then derive rate/efficiency metrics locally from the aggregated numerators:

- CPA = `spend / conversion`
- CVR = `conversion / clicks`
- CTR = `clicks / impressions`
- CPM = `spend / impressions * 1000`
- CPV = `spend / video_play_actions`

Prefer local derived values over averaging row-level rates, because the same material can appear
under multiple Smart+ Ads. Use these metrics to explain the Ad-level result, not to replace it.

## Winner Types

Do not define "best material" with a single sort. Default to three business labels:

| Winner type | Default read |
|---|---|
| Scale champion | Most primary outcomes, such as conversions, installs, leads, purchases, or video views. It may have higher CPA/CPV. |
| Efficiency champion | Lowest CPA/CPV/CPL among non-tiny samples. It may not be the biggest scale driver. |
| Overall winner | Enough primary outcomes and clearly better efficiency than the same-objective material or Ad benchmark. |

If material enrichment clarifies why an Ad-level candidate is strong by one label but weak by
another, keep the labels separate. For example:

```text
Ad A is the scale champion at Ad grain. Material context shows Material B contributed most
conversions inside that Smart+ delivery, while Material C had better CPA but smaller volume.
```

## Sample Guardrail

Use the adaptive evidence tiers from `references/candidate-discovery.md` after material
aggregation. A material with 1-2 conversions can be a directional observation, but should not
override the Ad-level winner/dragger classification.

## Fallback Pattern

If Smart+ material enrichment cannot be used:

```text
Smart+ material enrichment was unavailable in this environment, so the result is Ad-level
creative/ad benchmark. It can identify strong Ads, but it cannot fully separate multiple materials
inside the same Smart+ Ad.
```
