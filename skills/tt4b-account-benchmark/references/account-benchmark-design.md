# Account Benchmark Design

## Goal

Account-level benchmark provides an advertiser-specific baseline. It compares one current analysis
target against the same advertiser's historical performance, without requiring industry-wide
bottom-table computation.

## Data Model

Two datasets are conceptually separate:

| Dataset | Purpose | Default |
|---|---|---|
| Analysis dataset | The single Campaign, Ad Group, or Ad the user is currently inspecting | Last 7 complete days, Campaign level |
| Benchmark dataset | The account baseline used for comparison | Same number of complete days as analysis, same entity level as analysis |

They may be fetched in one broader API call and split locally, but the product semantics should
still treat them as two windows. In normal operation, fetch the analysis dataset and benchmark
dataset in parallel because they are independent read-only report calls.

The analysis dataset must resolve to one target entity. If a report pull returns multiple rows,
select the requested entity by ID/name, pick one cost-active entity for tests, or compute separate
benchmark verdicts per row. Do not aggregate multiple Campaigns, Ad Groups, or Ads into one
analysis target for a benchmark verdict.

## Entity Grain

Benchmark comparisons must be like-for-like. This is a product rule, not an implementation detail.

| Analysis view | Benchmark pool |
|---|---|
| Campaign | Cost-active Campaigns from the same advertiser |
| Ad Group | Cost-active Ad Groups from the same advertiser |
| Ad / Creative | Cost-active Ads from the same advertiser |

Do not compare a Campaign against Ad-level rows, or an Ad against Campaign-level rows. The user-facing
statement should read like:

```text
This campaign's CPC is better than 72% of cost-active campaigns from the same 7-day window.
This campaign's CPA is worse than 88% of cost-active campaigns from the same 7-day window.
This ad's spend is higher than 75% of cost-active ads from the same 7-day window.
```

For additive volume metrics, raw period totals are only directly comparable when the windows have
the same length. If the analysis window and benchmark window differ, use average daily values as
the default comparison.

Additive metrics include spend, impressions, clicks, conversions, video view counts, and engagement
counts. When the benchmark window is longer than the analysis window, for example when the user
asks to extend the benchmark to 30 days, compare a 7-day target spend to each benchmark entity's
30-day spend divided by 30, not to its raw 30-day spend.

Ratio and efficiency metrics should not be converted to daily values. CPC, CPA, CPM, CTR, CVR, ROAS,
and similar rates should be computed from the selected window's aggregated numerator and denominator,
then compared as rates.

## Default Windows

Use a same-length benchmark window by default:

| User analysis window | Benchmark window |
|---|---|
| 1-13 days | Same number of complete days |
| 14-30 days | Same number of complete days |
| User explicitly asks longer baseline | Use the requested longer window and daily-normalize additive metrics |

Avoid using today for either window by default because current-day data is incomplete. If the
same-length benchmark sample is too small, front-load a sample-size caveat and offer a longer
benchmark window such as 30 days as a follow-up.

## Cost Active

Default pool:

```text
spend > 0
```

Optional stricter pools:

```text
spend >= 1
spend >= 10
impressions >= 1000
```

Show same-grain sample counts in every output:

```text
Benchmark sample: 19 cost-active campaigns / 627 total campaigns
```

## Metric Eligibility

Do not use the same denominator for every metric.

| Metric | Eligibility | Business interpretation |
|---|---|---|
| CPC | spend > 0 and clicks > 0 | Lower is better |
| CPA | spend > 0 and conversion > 0 | Lower is better |
| CPM | spend > 0 and impressions > 0 | Lower is better |
| CTR | impressions > 0 | Higher is better |
| CVR | clicks > 0 | Higher is better |
| ROAS | spend > 0 and revenue/conversion_value > 0 | Higher is better |
| Spend | spend exists | Scale signal, not automatically good or bad |
| Impressions | impressions exists | Delivery scale signal, not automatically good or bad |
| Clicks | clicks exists | Traffic scale signal; direction depends on goal and quality |
| Conversions | conversion exists | Higher is better for conversion-focused campaigns |

For CPA, exclude zero-conversion rows from percentile computation, and separately report the
share of cost-active entities with zero conversions.

## Statistics

Compute two families of statistics, always at the same entity grain as the analysis view:

1. Blended account average.
   - CPC = total spend / total clicks
   - CPA = total spend / total conversions
   - CPM = total spend / total impressions * 1000
   - CTR = total clicks / total impressions * 100
   - CVR = total conversions / total clicks * 100
   - Additive volume metrics = average of per-entity daily values when windows differ.

2. Entity distribution percentiles.
   - Compute per-entity metric values at the selected grain.
   - Return P25, P50, and P75.
   - Return percentile rank for the current entity when an entity ID is being analyzed.
   - For lower-is-better metrics, top 25% threshold is P25.
   - For higher-is-better metrics, top 25% threshold is P75.

## Confidence

Keep these labels as internal calculation fields only. Human-facing output should translate them
into the sample caveat language in `references/analysis-output.md`.

| Eligible sample count | Confidence |
|---:|---|
| 0 | unavailable |
| 1-9 | low |
| 10-29 | medium |
| 30+ | high |

## Output Pattern

```text
[Account Benchmark]
Analysis window: 2026-06-01 to 2026-06-07, Campaign level
Benchmark window: 2026-06-01 to 2026-06-07, Campaign level
Benchmark pool: spend > 0
Sample: 19 cost-active campaigns / 627 total campaigns

Metric        Current   Median   Relative position                 Business read
CPC           $0.79     $0.88                   Better than 72% of campaigns      More efficient than median
Spend / day   $520      $360                    Higher than 82% of campaigns      High delivery/investment level
Conversions   48        35                      Better than 70% of campaigns      Strong conversion volume
CPA           $210      $95                     Worse than 88% of campaigns       Low-waterline dragger
```

## Official Benchmark Endpoint

`report_ad_benchmark_get` exists but should not be the primary implementation path.

Observed constraints:
- latency: 30-48 hours
- compare windows: 7, 14, 30, 60 days
- each compared object needs at least 1,000 impressions
- output may be empty even for high-impression objects

Use it only as optional enrichment. If it returns empty metrics, continue with local account
benchmark.
