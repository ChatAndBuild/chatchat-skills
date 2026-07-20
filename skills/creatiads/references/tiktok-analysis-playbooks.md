# TikTok Analysis Playbooks

Use these playbooks for TikTok diagnosis after MCP initialization. They fill the analysis behavior for advertiser classification, metrics, landing/app path, audience, creative fatigue, budget/bid, and measurement.

For deeper task-specific rules, use:

- [vertical-metric-playbooks](vertical-metric-playbooks.md)
- [vertical-report-templates](vertical-report-templates.md)
- [audience-optimization](audience-optimization.md)
- [creative-analysis](creative-analysis.md)
- [landing-page-and-funnel](landing-page-and-funnel.md)
- [budget-and-bid-optimization](budget-and-bid-optimization.md)
- [measurement-and-attribution](measurement-and-attribution.md)
- [error-cache-degradation](error-cache-degradation.md)

## Advertiser Type Classification

Run classification when the user asks what type an account is, when report context is missing, or before vertical-specific recommendations.

### Evidence Order

1. Recent top-spend advertiser, campaign, ad group, ad, and Smart+ rows.
2. Objectives, optimization goals, promotion type, campaign automation type, and result metric.
3. Landing URLs, app IDs, store URLs, catalog/shop evidence, identity evidence, and product evidence.
4. App event, pixel event, catalog, and custom conversion health.
5. Optional page/app content summaries when user supplied URLs or when MCP returns accessible destinations.

### Type Taxonomy

Return top candidates from:

- `short_drama`
- `ecommerce`
- `utility_or_w2a`
- `regulated_high_risk`
- `agency_or_mixed`
- `casual_game`
- `social`
- `novel`
- `midcore_or_hardcore_game`
- `search_arbitrage`
- `entertainment`
- `earnings_or_offerwall`
- `financial_leads`
- `unknown`

### Output

```json
{
  "top_types": [
    {"type": "ecommerce", "score": 0.82, "confidence": "high"}
  ],
  "evidence": {
    "objectives": [],
    "landing_urls": [],
    "store_urls": [],
    "app_names": [],
    "catalog_or_shop": [],
    "metric_evidence": []
  },
  "data_gaps": [],
  "recommended_metric_preset": "..."
}
```

## Metric Probe And Presets

Run `probe_metrics` when a key metric is missing, when onboarding a new advertiser, or before a formal vertical report.

Profiles:

| Profile | Use |
| --- | --- |
| `light` | core health: impressions, clicks, spend, conversions/results, value/revenue |
| `batch` | multi-account comparison and standardization |
| `vertical` | normal account diagnosis for the resolved advertiser type |
| `full` | connector QA, missing core value metric, or explicit support map request |

Probe groups should cover, when supported by the MCP report tools:

- core delivery
- web events
- app events
- shop and onsite commerce
- live
- messaging
- offline events
- creative/video
- attribution windows: click-through, view-through, engaged-view
- SKAN
- SAN
- placement, geo, device, and demographic attributes

Interpretation:

- `active`: returned usable non-zero or non-empty data.
- `supported_empty`: field returned but has no data for the selected window.
- `unsupported`: API rejects the field, dimension, level, product, or permission combination.
- `invalid_combination`: metric and dimension cannot be requested together.

Reports must not build conclusions on `unsupported` fields. If revenue/value is absent after a relevant probe, label the report as measurement-limited.

## Landing Page, SKU, And App Path

Use this for ecommerce page ranking, W2A analysis, SKU performance, and redirect quality.

Evidence chain:

1. Pull ad-level and Smart+ ad-level rows by spend.
2. Prefer report-level `ad_url` or destination attributes when returned.
3. For regular ads, enrich with ad detail and ad group detail.
4. For Smart+ campaigns, enrich with Smart+ campaign/ad detail.
5. For upgraded Smart+ creative rows, keep both report `ad_id` and upgraded Smart+ ad identity when available.
6. Extract `landing`, `app_store`, `deeplink`, `product`, `catalog`, `shop`, `creative_asset`, and `unknown` URL evidence separately.
7. Canonicalize landing URLs by scheme, host, path, product/SKU keys, and campaign-safe query parameters; keep this canonicalize step stable across daily and weekly reports.
8. Keep TikTok CDN or media URLs out of landing-page grouping; store them only as creative evidence.

W2A/app evidence:

- Adjust, Appsflyer, OneLink, Branch, or similar deferred deep-link domains.
- Self-owned domains that redirect to App Store or Google Play.
- App ID, app name, app download URL, app events, or campaign promoted app fields.

Output:

- URL/SKU/app ranking by spend, clicks, conversions/results, value, cost per result, and ROAS when active.
- `no_url` or unresolved object list with spend share.
- W2A classification and metric preset implication.
- Broken, mismatched, or suspicious redirect notes.

## Audience Breakdown

Use explicit breakdowns before generic audience commentary.

Required lenses:

- country or geo
- age and gender
- placement
- platform/device

Use `AUDIENCE` report routes when required by TikTok dimensions. If a combination fails, split the request into narrower dimensions and mark the rejected combination as `unsupported`.

Segment tags:

- `scale`
- `monitor`
- `reduce`
- `weak_cvr`
- `cheap_click_trap`
- `no_result_spend`
- `neutral`

Output should include `top_problem_segments`, `scale_candidates`, `cheap_click_traps`, supported dimensions, unsupported combinations, and follow-up probes.

## Creative Fatigue And Retention

For creative fatigue, use ad-level or Smart+ creative-level rows first, then enrich only the top candidates.

Required metrics when available:

- spend, impressions, clicks, conversions/results, value
- CTR, CPC, CPM, cost per result
- reach and frequency
- video plays
- 2s watched
- 6s watched
- p25, p50, p75, p100 video views
- average play time
- engaged-view or 15s engaged view

Derived metrics:

```text
hook_rate = p25 / video_plays
early_watch_rate = watched_2s / impressions
six_second_watch_rate = watched_6s / impressions
mid_retention = p50 / p25
deep_retention = p75 / p50
completion_rate = p100 / video_plays
conversion_from_play = conversions / video_plays
cost_per_retained_viewer = spend / watched_6s
```

Output:

- creative winners
- fatigue candidates
- high-spend low-conversion watchlist
- high-click low-retention watchlist
- replacement priority
- preview availability and missing preview sources

## Budget And Bid

Never execute budget or status changes without approval.

Action bands:

| Band | Evidence | Recommendation |
| --- | --- | --- |
| `scale` | stable spend, efficient cost, active vertical metric | increase 10-20% or duplicate plan after approval |
| `maintain` | efficient but limited evidence | keep and monitor |
| `fix` | mixed evidence | creative, audience, placement, bid, or landing fix |
| `reduce` | inefficient with enough spend | reduce 10-30% after approval |
| `pause` | high spend and no result or assist evidence | pause only after approval |

Return an action table with entity, spend, current KPI, diagnosis, recommendation, approval requirement, and confidence.

## Measurement And Attribution

Use this when numbers conflict, revenue is missing, or app/web paths are mixed.

Check:

- attribution window compatibility
- click-through, view-through, and engaged-view metrics
- SKAN delays or privacy thresholds
- SAN availability
- result/cost-per-result mismatches when ad groups have mixed goals
- W2A redirects that lose web context
- metrics returning `-`, empty, or invalid under a level/product combination

Return which metrics are decision-grade, which are directional, which are unavailable, and what configuration or probe should happen next.
