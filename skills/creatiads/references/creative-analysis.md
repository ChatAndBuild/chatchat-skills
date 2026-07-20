# Creative Analysis

Use this reference for creative fatigue, video funnel, placement/format mismatch, preview enrichment, and replacement priority.

## Required Metrics

Core:

- impressions, clicks, spend, conversion/result, revenue/value
- CTR, CPC, CPM, CPA or cost per result, CVR
- reach and frequency when available
- campaign, ad group, ad, creative, name, and objective context

Video:

- 2s and 6s watched when available
- p25, p50, p75, p100 or equivalent quartiles
- average play time
- engaged view or 15s engaged view when available

Preview:

- inline image or `Unavailable`
- hover/focus/click action for preview, playable, video, image, cover, Spark post, or equivalent MCP evidence
- For TikTok, read [tiktok-creative-preview-resolution](tiktok-creative-preview-resolution.md) and do not treat non-URL asset/Spark references as fetched previews.

## Derived Metrics

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

Compute only when denominators are present and non-zero. Otherwise mark the metric `not_available`.

## Fatigue Signals

| Signal | Interpretation |
| --- | --- |
| Frequency up and CTR down | fatigue or saturation |
| CPM up and CTR down | auction pressure or quality loss |
| p25 ok but p50/p75 weak | mid-message problem |
| completion strong but clicks weak | CTA or product mismatch |
| clicks strong but conversions weak | landing/app/store mismatch |
| high spend and zero result | refresh, narrow diagnosis, or pause candidate after approval |

## Output

Return:

- creative winners
- fatigue candidates
- high-spend low-conversion watchlist
- high-click low-retention watchlist
- video drop-off diagnosis
- replacement priority
- preview coverage and missing preview sources
- refresh brief with evidence

Do not scan the whole account for previews by default. Choose final report rows from insights first, then enrich those rows only.
