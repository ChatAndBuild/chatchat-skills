# Candidate Discovery

Use this guide when the user asks for high-CVR creatives, best ads, low-CPA ads, scalable ads,
hot objects, underperformers, or draggers. Discovery is not a replacement for benchmark. It is the
candidate generation step before same-grain benchmark interpretation.

## Core Rule

Sorting alone is not an answer. A candidate is only a recommendation after it is compared against
the same advertiser's same-objective, same-grain benchmark pool.

Default discovery is two-sided. Surface both:

- `Winners`: objects meaningfully above the account waterline.
- `Draggers`: objects with meaningful spend/traffic/outcome scale but weak objective-specific
  efficiency or quality versus the same benchmark pool.

Do not wait for a second user prompt to identify draggers when the pool is already loaded.

Examples:

- High-CVR Ad candidate -> benchmark against cost-active Ads in the same objective bucket.
- Low-CPA Ad Group candidate -> benchmark against cost-active Ad Groups in the same objective bucket.
- Strong Campaign candidate -> benchmark against cost-active Campaigns in the same objective bucket.
- Smart+ creative candidate -> benchmark at Ad grain; optionally enrich with `main_material_id`
  context when the Smart+ material report is available.

Do not use Campaign-level overview to judge Ad-level candidates.

## Candidate Unit

For creative/ad analysis, use Ad grain as the main candidate unit and benchmark key, including
Smart+ campaigns. Use `ad_id` for the main benchmark and aggregation key.

If the Campaign is `UPGRADED_SMART_PLUS`, `smart_plus_material_report_overview_run` may be used as
optional enrichment. In that enrichment only, use `main_material_id` as the material aggregation
key. Read `references/smart-plus-material-benchmark.md` before using the enrichment.

- Do not aggregate by `ad_name`; names can repeat and are not stable.
- Do not aggregate Smart+ material enrichment by `main_material_name`; use `main_material_id`.
- If `creative_id`, `video_id`, asset group, or similar fields are available, include them as
  descriptive context only. Do not use `creative_id` as the benchmark key or Ads Manager filter
  value. The finest supported user-facing benchmark unit is Ad grain, and Ad-grain object names
  are not linked to Ads Manager.
- If one Ad ID contains multiple asset groups or creative IDs and the BASIC report path cannot
  split them, say that the benchmark is Ad-level, not asset-group-level.

## Adaptive Evidence Tiers

Avoid a single fixed threshold such as `clicks >= 100` for every account. Accounts differ too much
by size, window length, and delivery pattern. Use the already fetched same-grain benchmark pool to
calculate soft evidence tiers locally, so this does not require extra API calls.

Recommended default:

1. Build the evidence pool from same-grain cost-active rows.
2. For CVR-sensitive discovery, compute click and conversion distribution among rows with clicks
   and conversions.
3. Set adaptive reference points:
   - `median_clicks = P50(clicks among click-positive rows)`
   - `median_conversions = P50(conversions among conversion-positive rows)`
4. Classify each candidate:
   - `main_candidate`: has meaningful evidence for this account/window, usually at or above the
     account's median clicks and median conversions, or has strong conversion volume even if one
     threshold is slightly below median.
   - `observation_candidate`: has positive conversions or a strong rate but is below below-median
     evidence.
   - `tiny_sample`: has only 1-2 conversions or very few clicks; do not put it in the main
     recommendation bucket.

If no object qualifies as `main_candidate`, say so directly and show the best directional
observations with a sample warning. Do not relax the evidence threshold silently until a tiny-sample
object looks like a recommendation.

## Good Candidate Types

Separate good candidates by business reason:

| Candidate type | Strong signal | Watch-out |
|---|---|---|
| High CVR | CVR better than most comparable objects and enough clicks/conversions | Can be tiny-sample or low-scale |
| Low CPA | CPA better than most comparable objects with non-trivial conversions | CVR may be average, but cost efficiency is strong |
| High scale | Conversions/spend/clicks higher than most comparable objects | May not be high CVR; interpret as scalable rather than best rate |
| Scale champion | Highest primary outcome volume for the objective | May be expensive; do not call it best overall without efficiency |
| Efficiency champion | Best CPA/CPV/CPL among non-tiny samples | May be too small to scale |
| Overall winner | Meaningful primary outcome volume and clearly better efficiency than benchmark | Needs both scale and efficiency evidence |

Do not collapse these into one generic "best creative" list unless the user explicitly asks for a
combined score. Prefer separate sections because each type answers a different business question.

## Dragger Discovery

Draggers are not simply "the highest CPA" or "the lowest CVR" rows. They are objects that have
enough scale to matter and are weak versus comparable objects for the selected objective.

Use the same evidence pool as winner discovery:

1. Start from cost-active rows in the same advertiser, objective, grain, and window.
2. Exclude tiny spend / tiny click / tiny outcome rows from the main dragger list. Put them in
   directional observations if they are interesting.
3. Compare both contribution and efficiency:
   - spend share versus primary outcome share
   - core efficiency metric versus median
   - rate/quality metric versus median
4. Classify draggers:
   - `current_dragger`: enabled/live object with meaningful scale and weak efficiency.
   - `historical_dragger`: disabled/stopped object that hurt the window but is not currently live.
   - `directional_risk`: weak metric but low scale or small sample.
5. Attach a user-facing benchmark waterline to every surfaced dragger:
   - Conversion: "CPA 差于 / worse than N% of comparable {grain}s" and/or "CVR 弱于 / weaker than N%."
   - Traffic: "CPC 差于 / worse than N%" and/or "CTR 弱于 / weaker than N%."
   - Reach/Awareness: "CPM 差于 / worse than N%" or "delivery scale lower than N% for this spend level."
   - Video: "CPV 差于 / worse than N%" or "6s view / completion weaker than N%."
   If percentile/rank evidence is unavailable for the metric, say the dragger is partial and do
   not present it as a fully benchmarked dragger.

Objective-specific defaults:

| Objective | Main dragger signals |
|---|---|
| Conversion | Spend/click scale is meaningful, CPA worse than comparable objects, CVR below median, or spend share materially exceeds conversion share. |
| Traffic | CPC above median, CTR below median, or spend share materially exceeds click/landing-page-view share. |
| Reach/Awareness | CPM above median, exposure/reach scale weak for the spend, or frequency looks inefficient when available. |
| Video | CPV above median, 6s view / completion weak, or spend share exceeds video-view contribution. |
| App/Lead/Product Sales | Use the objective's primary cost and outcome metrics; avoid click-only dragger verdicts. |

Draggers should be written as read-only diagnosis evidence, not as write instructions. Say
"优先排查/复查" rather than "pause this" unless the user explicitly moves into a management skill.

## Winner And Dragger Presentation

Candidate output is a same-grain pyramid, not a mixed object dump:

1. State the benchmark pool and grain.
2. Introduce Winners as the high-waterline group.
3. Introduce Draggers as the low-waterline group.
4. Show one grain per table. Campaign rows go in Campaign tables, AdGroup rows go in AdGroup
   tables, and Creative rows go in Creative tables.

Every Winner row must include:

```text
object name, status, spend, primary outcome, core efficiency metric,
benchmark waterline such as "CPA better than 92% of comparable Ad Groups",
business read.
```

Every Dragger row must include:

```text
object name, status, spend, primary outcome, core efficiency metric,
benchmark waterline such as "CPA worse than 88% of comparable Ad Groups",
business read.
```

Do not rely on wording like "CPA is above account average" for the main rows. Account average is
useful context, but the skill's differentiator is the same-account relative benchmark level.

## Status Context

Status is a default read-only enrichment for candidate outputs. Before calling a surfaced object a
winner, hot object, scalable candidate, or "worth watching", attempt status lookup for the object
and relevant parent objects:

- Campaign candidate -> Campaign status.
- Ad Group candidate -> Ad Group status and parent Campaign status.
- Ad candidate -> Ad status, parent Ad Group status, and parent Campaign status.
- Smart+ creative candidate -> Ad status plus parent Ad Group/Campaign status. If optional
  material enrichment exposes linked Smart+ objects, use them only as status context.

Use read/list/status-get tools only. Never call status update tools from this benchmark skill.

- Active/enabled candidates can stay in the main recommendation bucket.
- Disabled/stopped candidates should be downgraded or clearly marked: "performance looked strong,
  but this object is currently stopped; inspect the stop reason before reuse or scaling."
- If status is not available from the current report path, say status was not checked rather than
  assuming the object is live.

Status lookup should be attempted when the host/tooling exposes read tools. A missing status lookup
should not block the benchmark result, but it must change the wording from an immediate scaling
recommendation to a conditional read: "状态未能通过当前 MCP 工具查到，所以这个扩量判断需要先补状态确认。"
Do not tell the user "扩量前最好再确认状态" unless you first attempted the status lookup or clearly
say the available MCP schema did not expose a safe read status tool.

## Output Pattern

For each candidate, explain the combined business judgment:

```text
High CVR candidate:
Ad 123 has CVR better than 94% of comparable Ads, CPA better than 81%, and enough evidence for
this account/window. This looks like a real high-intent candidate.

Directional observation:
Ad 456 has very high CVR, but only 2 conversions and 11 clicks. Treat it as a weak signal rather
than a reusable winner.

Low CPA scale candidate:
Ad 789 is not high-CVR, but CPA is better than 88% of comparable Ads and conversion volume is among
the highest in the account. Treat it as a cost-efficient scale candidate, not a high-CVR creative.

Smart+ enrichment context:
Ad 789 is the Ad-level overall winner. Optional material enrichment shows Material
7595719967740284173 contributed most conversions behind that Ad, but the benchmark verdict remains
Ad-level.
```
