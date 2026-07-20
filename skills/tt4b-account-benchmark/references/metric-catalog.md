# Metric Catalog

Use this catalog to translate user-facing metric names into report API metric keys and local
benchmark computation keys. The API-facing key is the value to place in `metrics`.

This catalog is scoped first to the BASIC `report_integrated_get` path used by account benchmark,
with endpoint-specific overrides for verified adjacent enrichment paths such as Smart+ material
reporting.
Do not assume one endpoint's metric key works on another endpoint.

## Core Metrics

| User-facing name | API metric key | Local compute key | Default | Type | Business interpretation | Notes |
|---|---|---|---|---|---|---|
| Spend / Cost / 消耗 | `spend` | `spend` | Yes | Additive scale | Scale signal; not automatically good or bad | Daily-normalize when windows differ |
| Impressions / 展示 | `impressions` | `impressions` | No | Additive scale | Delivery scale signal; not automatically good or bad | Daily-normalize when windows differ |
| Clicks / 点击 | `clicks` | `clicks` | No | Additive traffic | Usually positive for traffic goals, but still a scale signal | Daily-normalize when windows differ |
| Conversions / 转化 | `conversion` | `conversion` | Yes | Additive volume | Higher is better | API response observed as `conversion`, not `conversions` |
| CPC | `cpc` | `cpc` | Yes | Efficiency rate | Lower is better | Prefer local `spend / clicks` when raw numerators exist |
| CPA / Cost per Conversion | `cost_per_conversion` | `cost_per_conversion` | Yes | Efficiency rate | Lower is better | Exclude zero-conversion rows from percentile values |
| CPM | `cpm` | `cpm` | Yes | Efficiency rate | Lower is better | Prefer local `spend / impressions * 1000` |
| CTR | `ctr` | `ctr` | Yes | Rate | Higher is better | Prefer local `clicks / impressions * 100` |
| CVR / Conversion Rate | `conversion_rate` | `conversion_rate` | Yes | Rate | Higher is better | Prefer local `conversion / clicks * 100` |

## Extended Metrics

| User-facing name | API metric key | Local compute key | Default | Type | Business interpretation | Notes |
|---|---|---|---|---|---|---|
| Video Plays | `video_play_actions` | `video_play_actions` | No | Additive volume | Higher depends on goal | Daily-normalize when windows differ |
| 2s Video Views | `video_watched_2s` | `video_watched_2s` | No | Additive volume | Higher depends on goal | Daily-normalize when windows differ |
| 6s Video Views | `video_watched_6s` | `video_watched_6s` | No | Additive volume | Higher depends on goal | Daily-normalize when windows differ |
| Video 25% | `video_views_p25` | `video_views_p25` | No | Additive volume | Higher is usually better | Daily-normalize when windows differ |
| Video 50% | `video_views_p50` | `video_views_p50` | No | Additive volume | Higher is usually better | Daily-normalize when windows differ |
| Video 75% | `video_views_p75` | `video_views_p75` | No | Additive volume | Higher is usually better | Daily-normalize when windows differ |
| Video 100% / Completed Views | `video_views_p100` | `video_views_p100` | No | Additive volume | Higher is usually better | Daily-normalize when windows differ |
| Profile Visits | `profile_visits` | `profile_visits` | No | Additive volume | Higher is usually better | May be permission/account dependent |
| Follows | `follows` | `follows` | No | Additive volume | Higher is usually better | May be permission/account dependent |
| Likes | `likes` | `likes` | No | Additive volume | Higher is usually better | Engagement metric |
| Comments | `comments` | `comments` | No | Additive volume | Higher is usually better | Engagement metric |
| Shares | `shares` | `shares` | No | Additive volume | Higher is usually better | Engagement metric |

## Objective-Specific Metrics

These metrics may be needed for objective-aware profiles, but availability varies by endpoint and
account permission. Request them only when the selected endpoint supports them; otherwise remove
the unsupported field and explain the fallback.

| Objective area | Preferred metrics | Fallback when unavailable |
|---|---|---|
| App promotion | `app_install`, `cost_per_app_install`, or `conversion`, `cost_per_conversion` | Use `conversion` and `cost_per_conversion`, and say install-specific metrics were unavailable |
| Lead generation | `form`, `sales_lead`, `cost_per_form`, `cost_per_sales_lead`, `form_rate` | Use supported lead outcome metric if present; otherwise avoid lead-cost verdict |
| Reach/Awareness | `impressions`, `reach`, `frequency`, `cpm` | Use `impressions` and `cpm`; say reach/frequency were unavailable |
| Traffic | `clicks`, `landing_page_view`, `cpc`, `ctr` | Use `clicks`, `cpc`, `ctr` |
| Video views | `video_play_actions`, `video_watched_6s`, `video_views_p100`, `cost_per_video_view` | Use supported video view counts and derive CPV locally if possible |
| Product sales / Shop | `complete_payment`, `purchase`, `cost_per_purchase`, `product_clicks` | Use supported purchase metric; avoid revenue metrics on BASIC unless verified |

## Endpoint-Specific Mapping

| Endpoint/report path | CVR key | Material key | Notes |
|---|---|---|---|
| BASIC `report_integrated_get` | `conversion_rate` | none | Current primary path for Campaign, Ad Group, and Ad benchmark |
| Smart+ material `smart_plus_material_report_overview_run` | `conversion_rate_v2` | `main_material_id` | Optional enrichment only; use `main_material_name` and `main_material_type` as context |

For Smart+ material enrichment, prefer additive numerators (`spend`, `clicks`, `conversion`,
`impressions`) and derive CPA/CVR/CTR locally after aggregating by `main_material_id`; keep the
main benchmark verdict at Ad grain.

If an endpoint returns a 400/invalid field error for a metric:

1. Remove that metric from the request.
2. Retry the same read-only request once if the remaining metric set still answers the question.
3. Explain which metric was dropped and which fallback metric or local derivation is being used.

## Aliases

Accept these user aliases and normalize them locally:

| User says | Normalize to |
|---|---|
| `conversions` | `conversion` |
| `cpa` | `cost_per_conversion` |
| `cost per result` when the result is conversion | `cost_per_conversion` |
| `cvr` | `conversion_rate` |
| `cvr` on Smart+ material enrichment | `conversion_rate_v2` |
| `cost` | `spend` |

## Unsupported Until Verified

| User-facing name | Do not request as | Reason |
|---|---|---|
| Real-time conversions | `real_time_conversions` | Listed in a generic reporting skill, but not yet verified for this benchmark path |
| Revenue / GMV / conversion value | unknown | Needs a verified commerce/revenue metric before ROAS can be benchmarked |

When the user asks for unsupported metrics, explain that the current benchmark path cannot request
that metric yet, then offer to run the supported core benchmark or investigate the correct endpoint.

Unsupported metric response pattern:

```text
当前 benchmark 的 BASIC 报表路径暂未验证 revenue/commerce 类指标，所以我不会把
这类字段放进这次 report_integrated_get 请求里。可以先用 Spend、Conversions、
CPA、CPC、CPM、CTR、CVR 做账户内 benchmark；如果你一定要收入类指标，我需要先确认可用的
commerce/revenue 报表端点。
```

If the user asks only for unsupported metrics and no supported fallback remains, stop and explain
the limitation instead of running an unrelated benchmark.

## Display Rules

- Show user-facing names in prose and tables.
- Show endpoint metric field names only when explaining implementation, debugging, or writing a
  request preview.
- Keep metric direction visible for benchmark interpretation: lower CPC/CPA/CPM is better; higher
  CTR/CVR/conversions is better for conversion or traffic goals. Spend and impressions are scale
  signals, not automatically "good" or "bad" without the user's objective.
- Translate statistical fields into advertiser language by default: use "median",
  "better than N% of comparable objects" for strong rows, "worse/weaker than N% of comparable
  objects" for weak rows, or "higher/lower than N% of comparable objects" for neutral scale
  signals instead of P25/P50/P75 terminology.
