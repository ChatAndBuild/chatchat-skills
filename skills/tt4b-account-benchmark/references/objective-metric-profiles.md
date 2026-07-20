# Objective Metric Profiles

Use this reference before selecting metrics, benchmark pools, and conclusion language. The default
benchmark pool must match all three dimensions:

```text
same objective_type + same grain + same window
```

Do not compare a `REACH` Campaign against `WEB_CONVERSIONS` Campaigns, and do not use a Campaign
benchmark to judge an Ad or material candidate.

## Resolution Order

1. Resolve the target object's `objective_type` before the main benchmark request whenever the
   API/tooling supports it.
2. At Campaign grain, use the Campaign's own `objective_type`.
3. At Ad Group or Ad grain, use the parent Campaign `objective_type` when row-level objective is
   absent.
4. For account overview, split rows into objective buckets and render each bucket with its own
   profile. Keep an account total as a scale summary only.
5. If objective lookup fails, continue only when the requested question can be answered with
   neutral or explicitly requested metrics. State that objective context was not verified.

If the user asks for a conversion judgment but the resolved objective is `REACH`, `VIDEO_VIEWS`,
or another non-conversion objective, say so directly:

```text
这条 Campaign 是 REACH/Brand Awareness 目标，所以 0 转化不能直接说明表现差。
我会按品牌曝光目标看 CPM、曝光、Reach/Frequency，而不是默认用 CPA/CVR 下结论。
```

## Profiles

| Objective Type | Primary metrics | Supporting metrics | Do not default to |
|---|---|---|---|
| `WEB_CONVERSIONS` / `CONVERSIONS` | `conversion`, `cost_per_conversion`, `conversion_rate`, `spend` | `ctr`, `cpc`, `cpm`, `clicks` | Reach/Frequency as the core verdict |
| `APP_PROMOTION` | `app_install` or `conversion`, `cost_per_app_install` or `cost_per_conversion` | `clicks`, `cpc`, `ctr`, `cpm` | CTR-only judgment |
| `LEAD_GENERATION` | `form` or `sales_lead`, `cost_per_form` or `cost_per_sales_lead` | `form_rate`, `ctr`, `cpc` | Purchase or revenue judgment |
| `REACH` | `impressions`, `reach`, `frequency`, `cpm` | `video_play_actions`, `ctr` | CPA, CVR, conversion-first judgment |
| `TRAFFIC` | `clicks`, `cpc`, `ctr`, `landing_page_view` | `cpm`, `spend` | CPA except as post-hoc observation |
| `VIDEO_VIEWS` | `video_play_actions`, `video_watched_6s`, `video_views_p100`, `cost_per_video_view` | `engagement_rate`, `cpm` | Conversion-first judgment |
| `PRODUCT_SALES` / Shop | `complete_payment`, `purchase`, `cost_per_purchase` | `product_clicks`, `ctr`, `cpc` | Click-only judgment |

Only request a metric if `references/metric-catalog.md` marks it supported for the selected
endpoint. If a profile's ideal metric is unavailable, use the nearest supported metric and name
the limitation.

## Conclusion Language

Use objective-specific wording:

- Conversion campaigns: "CPA is lower/higher than the median conversion Campaign in this account";
  "CVR is better than N% of comparable conversion Campaigns."
- App campaigns: "cost per install/conversion is better/worse than comparable app-promotion
  objects"; "install or conversion volume is enough/not enough for a strong read."
- Lead campaigns: "cost per lead/form and lead volume are the primary verdict; CTR is supporting."
- Reach/awareness campaigns: "CPM is below/above the median brand Campaign; exposure and reach
  scale are sufficient/limited; frequency is efficient/high."
- Traffic campaigns: "CPC/CTR/click volume are better/worse than comparable Traffic objects; CPA
  is only a downstream observation."
- Video campaigns: "6s views, completions, and CPV are the core read; conversion is not the
  default verdict."
- Product Sales campaigns: "purchase volume and cost per purchase are the core read when supported;
  clicks only explain funnel traffic."

## Dragger Language

Use objective-specific dragger wording; do not reuse conversion dragger language for every
objective:

- Conversion campaigns: "This object is dragging the conversion pool because spend/click scale is
  meaningful, but CPA is worse than comparable conversion objects and/or CVR is below median.
  Check whether spend share exceeds conversion share."
- App campaigns: "This object is a dragger when install/conversion cost is worse than comparable
  app objects while install/conversion volume does not justify the spend."
- Lead campaigns: "This object is a dragger when CPL is worse than comparable lead objects or lead
  volume is weak for its spend."
- Reach/awareness campaigns: "This object is a dragger when CPM is inefficient or exposure/reach
  scale is weak for the spend. Do not call it a dragger because it has zero conversions."
- Traffic campaigns: "This object is a dragger when CPC is high, CTR is weak, or spend share
  exceeds click/landing-page-view contribution. CPA is only a downstream observation."
- Video campaigns: "This object is a dragger when CPV is high or 6s view / completion metrics are
  weak for the spend. Do not use conversion-first language by default."
- Product Sales campaigns: "Use purchase/payment volume and cost per purchase when supported; if
  purchase metrics are unavailable, avoid a hard commerce dragger verdict and state the limitation."

## Mixed Objective Account Output

For account overview or account benchmark requests, prefer this structure:

1. Account total: spend, impressions, clicks, conversions or primary outcomes as a scale summary.
2. Conversion benchmark: only conversion-objective Campaigns or rows.
3. Awareness/Reach summary: only awareness/reach rows.
4. Other objective buckets: traffic, app, video, lead, shop as present.
5. Campaign contributors: who contributed spend, primary outcomes, and poor efficiency within
   their own objective bucket.
6. Winners and draggers: who is above account waterline and who is pulling the objective bucket
   down. Keep the two sections separate.
7. Creative/material winners: only after candidate objects are benchmarked in the correct bucket.

Do not present one blended CPA/CVR verdict for an account that mixes conversion and awareness
Campaigns.
