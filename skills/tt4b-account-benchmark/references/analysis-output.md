# Analysis Output

Account benchmark should not stop at a metric table. Provide a concise narrative, but keep the
recommendations constrained by the user's selected objective and metrics. If `objective_type` is
known, the output must use objective-aware metrics and language from
`references/objective-metric-profiles.md`.

## Language And Artifact Policy

Match the user's primary language in the conversational answer and in any human-readable
`summary.md` artifact:

- Chinese or mostly Chinese mixed-language prompt -> Chinese response and Chinese `summary.md`.
- English prompt -> English response and English `summary.md`.
- Keep object names, IDs, metric acronyms, and API terms unchanged when they are clearer as-is.
- `result.json` and `manifest.json` stay machine-readable and do not need translated field names.

Artifacts supplement the answer; they do not replace it. Before linking `summary.md`,
`result.json`, or `manifest.json`, write the user-facing summary directly in the conversation.
After writing `summary.md`, inspect or reopen the saved file when the host allows it. If the
heading and main narrative language do not match the user's primary language, rewrite `summary.md`
before sending the final answer.
Prefer generating `summary.md` from the same localized narrative used in the chat answer. Do not
use a separate ad hoc English artifact template for Chinese prompts. If the chat answer is Chinese
but `summary.md` is English, the run is not complete yet.

For account overview, hot-object, or "热门 adg" style requests, the conversational answer must
include:

- window and grain
- benchmark sample size
- selected Campaign / AdGroup benchmark target as a linked object name when link fields are
  available; Ad-grain targets remain plain text
- benchmark table, benchmark verdict, and a compact benchmark scope appendix or one-line scope note
- enough grounded business reads to stand on its own; for ranked hot-object/candidate outputs,
  include at least 4-6 concise bullets covering winners, draggers, scale leader, efficiency
  leader, key risk, and what to look at next when those categories differ

Do not answer only with "saved result" or only with file links. The user should understand the
conclusion without opening `summary.md`.

## Reading Order And Labels

For Chinese or Chinese-dominant prompts, use Chinese-first headings. English benchmark terms may
appear once in parentheses for continuity with tooling, but do not mix English-first section names
with Chinese prose.

```text
结论先说
核心对比
基准结论
下一步建议
附录：基准范围
```

English output may use:

```text
Bottom line
Benchmark table
Benchmark verdict
Next steps
Appendix: Benchmark scope
```

This is a hard output contract, not a style preference. Do not replace these sections with only
"账号复盘", "整体表现", "重点 Campaign", "诊断", or "趋势". Those sections can appear only as
supplements after the benchmark result. Put benchmark scope at the end as a compact appendix or a
single small scope line; do not make metadata the first thing the reader sees. If a benchmark
cannot be computed, use:

```text
Benchmark blocked（Benchmark 受阻）
```

or:

```text
Partial benchmark（部分 Benchmark）
```

and explain the MCP/auth/permission/sample blocker.

## Conversation Summary Depth

Do not compress a multi-object benchmark into two or three sentences while saving a much richer
`summary.md`. The chat answer can be shorter than the artifact, but it must preserve the main
decision logic.

For hot Ad Group / hot Campaign / candidate discovery outputs, use this minimum structure in the
conversation:

```text
结论先说
- 第一句只给一个定性判断 + 一个最关键数字，不要把 Spend、Conversions、CPA、CVR、样本量全挤在一句话里。
- 其余指标紧跟在后面用 2-5 条短列呈现。

Winners（表现好）
- 导语：这些对象处在同 objective / 同 grain / 同窗口 benchmark pool 的较好水位，说明它们不是只靠绝对量看起来好。
| Campaign | Spend | Conversions/primary outcome | CPA | CVR | 其他已跑指标 | 定位 |

Draggers（拖后腿）
- 导语：这些对象处在同 objective / 同 grain / 同窗口 benchmark pool 的较弱水位，且规模足以影响账户结果。
| Campaign | Spend | Conversions/primary outcome | CPA | CVR | 其他已跑指标 | 定位 |

核心对比
| 指标 | 当前对象 | 中位数/均值 | 相对位置 | 业务判断 |

业务判断
- 3-5 条，说明可继续观察、需要验证、或不应误读的地方。

下一步建议
- 以下建议基于报表数据，执行前请结合实时投放状态确认。
- 分层给出观察 / 复核 / 可进入哪个只读或管理流程，不编造量化预期。

附录：基准范围
- 广告主 / 窗口 / 粒度 / 目标 / 基准池 / 样本。

已保存
- summary.md / result.json / manifest.json
```

For Chinese prompts, the saved `summary.md` should use Chinese headings such as:

```text
# 热门 Ad Group 基准
## 结论先说
## Winners（表现好）
## Draggers（拖后腿）
## 核心对比
## 基准结论
## 业务判断
## 下一步建议
## 状态检查
## 样本与口径 caveat
## 附录：基准范围
```

Avoid English-only headings like `Hot Ad Group Benchmark` or `Key Reads` in a Chinese `summary.md`.

## Sample Caveat

Before the metric table, include a plain-language caveat whenever the benchmark sample is small.
Do not show "Confidence" as a table column or ask the user to interpret a score. Treat confidence
as an output guardrail.

Suggested thresholds:

| Eligible sample | Output treatment |
|---:|---|
| 0 | No benchmark conclusion; explain that there are no eligible comparable rows. |
| 1-9 | Front-load: "请注意，目前有效样本量只有 N 个，结论更适合作为方向性信号，建议后续扩大窗口或切到更粗粒度再验证。" |
| 10-29 | Front-load: "请注意，目前有效样本量为 N 个，结论具备参考价值，但仍建议结合更长窗口验证。" |
| 30+ | No caveat required unless specific metrics have lower eligibility. |

If metric-specific eligibility differs, use the smallest important metric sample in the caveat,
especially for CPA/CVR where zero-conversion rows can reduce eligible samples.

## Object Labels

Every user-visible Campaign or AdGroup reference should use the linked object name when the
required link fields are available:

```text
[object_name](Ads Manager URL)
```

Examples:

```text
[Summer Prospecting - Web Conversions](https://ads.tiktok.com/i18n/manage/campaign?...)
[Unknown name](https://ads.tiktok.com/i18n/manage/adgroup?...)
Catalog carousel material
```

Do not show a standalone object `ID` column and do not use the legacy `{name} ({id})` style in
tables, bullets, winner lists, verdicts, or scope text. IDs should remain inside the Ads Manager
URL for Campaign / AdGroup links, or appear only in an explicit blocked/partial-link diagnostic.
Ad / Creative object names are plain text by design and should not include IDs by default.

For links, keep the Ads Manager sidebar filter shape and use the grain-specific link ID:
Campaign uses `campaign_id`; AdGroup keeps URL field `ad_ids` but uses the AdGroup identity
(`adgroup_id`, or `ad_id` only when that field names the AdGroup identity). Do not build
Ads Manager links for Ad / Creative grain, regardless of ordinary or Smart+ type. Keep
`creative_id`, `virtual_creative_id`, `smart_plus_ad_id`, and `ad_material_id` as context only.

Use the concrete grain as the first table column because each analysis output has one grain:

```text
| Campaign | Spend | Conversions/primary outcome | CPA | CVR | 定位 |
| AdGroup | Spend | Conversions/primary outcome | CPA | CVR | 定位 |
| Creative | Spend | Conversions/primary outcome | CPA | CVR | 定位 |
```

If the API or MCP response does not return a name field, use `[Unknown name](url)` for Campaign /
AdGroup rows when a link can be built. For Ad grain, use plain `Unknown name` and add a short note
that the name field was unavailable. Do not silently show bare IDs in tables, bullets, winner
lists, or contributor summaries.

Candidate, contributor, and winner lists must include object name, grain, objective, spend,
primary outcome, and core efficiency metric.

## Required Benchmark Blocks

Do not let trend or week-over-week analysis swallow the benchmark. Any final answer produced by
this skill must include the benchmark blocks below, unless the answer is explicitly labeled as a
benchmark-blocked or partial benchmark result. A WoW-only or raw-report-only final answer is not
compliant for this skill.

A benchmark answer must include these blocks when benchmark data was computed. The scope block
belongs after the conclusion and next steps unless the user explicitly asks for methodology first:

```text
核心对比
| 指标 | 当前对象 | 中位数 | 相对位置 | 业务判断 |
|---|---:|---:|---|---|

基准结论
- [Name](url) 在 {primary metric} 上好于/弱于 N% 的可比 {grain}；原因必须来自上面的表格。

附录：基准范围
- 广告主：{advertiser_name} ({advertiser_id})
- 窗口：{start_date} 到 {end_date}
- 粒度：Campaign / Ad Group / Ad
- 目标：{objective_type}
- 基准池：spend > 0 的 {grain}
- 样本：{eligible_count} eligible / {total_count} total
```

Winner and dragger rows are not complete without a relative waterline:

```text
Winner: [Name](url) - CPA better than 92% of comparable Campaigns.
Dragger: [Name](url) - CPA worse than 88% of comparable Campaigns.
```

Use same-grain wording. If the table is Campaign grain, every relative sentence says comparable
Campaigns. If it is Ad Group grain, every relative sentence says comparable Ad Groups. Do not mix
Campaign and Ad Group rows in one Winners/Draggers table.

Winners and Draggers must be tables, not dense paragraphs. Preserve full object names. Campaign
and AdGroup names should be linked when available; Ad / Creative names should remain plain text.
Do not truncate long names. The first table column is the concrete grain, not `Object` / `对象`,
and there is no standalone object `ID` column. Include every metric that was
actually computed as a visible column; do not crop metrics just to keep the table short. Format
money with thousands separators, such as `$2,222.13`. If a value is unavailable, show `-` or `—`
and keep the column. The `Median` column must state its statistic, usually
`中位数`; use `均值` only when the calculation actually uses a mean.

For account overview, separate trend from benchmark:

```text
WoW trend
- This week versus previous week: spend, impressions, clicks, primary outcomes, and key rates.

Account benchmark
- Same-window, same-objective, same-grain comparison using the required benchmark blocks above.
```

For account overview, the benchmark must be in the same response. If the user did not specify a
target object, state the auto-selected primary target before the benchmark blocks. Match the
field labels to the user's language:

```text
主基准对象
- 我选择了 [Summer Prospecting](url)，粒度 Campaign，目标 WEB_CONVERSIONS，因为它是这个窗口内主目标桶里消耗最高的有消耗 Campaign。

Primary benchmark target
- Selected [Summer Prospecting](url), Campaign, WEB_CONVERSIONS, because it is the highest-spend
  cost-active Campaign in the dominant objective bucket for this window.
```

If only WoW trend was computed and no benchmark pool exists, explicitly say:

```text
这段是 WoW trend，不是 benchmark；我还没有拿到同 objective / 同 grain / 同窗口的 benchmark pool。
```

Then stop or mark the response as partial; do not provide "good/bad", "worth scaling", or
"strong/weak" verdicts until a benchmark pool is available.

## Output Sections

For a single-object benchmark, use these sections after the sample caveat and benchmark table.
For Chinese output, keep the headings Chinese-first:

```text
现象
- What changed or where the target sits versus account history.

洞察
- Why the pattern likely matters, grounded only in the pulled metrics.

下一步建议
- Start with: "以下建议基于报表数据，执行前请结合实时投放状态确认。"
- Then give safe, read-only or decision-support actions. Avoid budget/creative/status changes
  unless the user explicitly asks to move into the relevant management skill.
```

For account overview or mixed-objective account benchmark, use this fixed structure:

```text
Account total
- Spend, impressions, clicks, and primary outcomes as an account-scale summary.

Winners
- Objects that are meaningfully better than comparable rows on objective-appropriate scale and
  efficiency. Start with a one-sentence intro that tells the user this group is above the account
  waterline, then show each row's "better than N% of comparable {grain}s" evidence.

Draggers
- Objects with meaningful scale but weak objective-specific efficiency or quality. Distinguish
  current enabled draggers from historical stopped draggers. Start with a one-sentence intro that
  tells the user this group is below the account waterline or pulling the bucket down, then show
  each row's "worse/weaker than N% of comparable {grain}s" evidence.

Conversion benchmark
- Only conversion-objective rows. Discuss conversion volume, CPA, CVR, spend, winners, and
  draggers.

Awareness/Reach summary
- Only reach/awareness rows. Discuss impressions, reach/frequency when available, and CPM.

Campaign contributors
- Who contributed spend, primary outcomes, and poor efficiency within its own objective bucket.

Creative/material winners
- Only after candidate discovery and same-objective benchmark. Split into scale champion,
  efficiency champion, overall winner, and draggers when weak objects materially affect the pool.
```

Omit empty objective buckets, but do not merge them into unrelated buckets.

## Phenomena

Phenomena are observable facts from the current result. They should reference:

- analysis window
- benchmark window
- entity grain
- sample size caveat when it affects interpretability
- advertiser-facing relative position, not raw percentile jargon
- volume/rate normalization method

Examples:

```text
- 请注意，目前有效样本量只有 8 个，结论更适合作为方向性信号，建议后续扩大窗口或切到更粗粒度再验证。
- CPC is better than 72% of comparable cost-active Ad Groups.
- Spend per day is higher than most comparable Ad Groups, while CTR is close to the account's
  median.
- CPA is unavailable because the benchmark sample has too few conversion-positive rows.
```

## Advertiser-Facing Metric Language

Keep P25/P50/P75 and percentile rank in the internal result object, but translate them in the
human-facing table and narrative:

| Internal statistic | Human-facing wording |
|---|---|
| `p50` / median | "median" |
| `percentileRank` for lower-is-better metrics | "better than N% of comparable objects" |
| `percentileRank` for higher-is-better outcome metrics | "better than N% of comparable objects" |
| `percentileRank` for scale metrics | "higher than N% of comparable objects" |
| top quartile | "among the strongest 25%" or "in the high end of account history" |

Avoid exposing "P25", "P50", "P75", "median", or "percentile" in the default response unless the
user asks for the diagnostic math.

For ranked candidate sections, use these section-level translations:

| Section | Required waterline language |
|---|---|
| Winners / 表现好 | "好于 / better than N% of comparable {grain}s" on the primary efficiency or outcome metric. |
| Draggers / 拖后腿 | "差于 / worse than N% of comparable {grain}s" or "弱于 / weaker than N%" on the primary efficiency or quality metric. |
| Scale-only leader | "规模高于 / higher than N%" and then state whether efficiency is also good or only average. |
| Neutral object | "接近中位数 / close to median" and avoid forcing it into Winners or Draggers. |

Do not leave relative position only in the general Benchmark table. The Winners and Draggers
sections themselves must carry the waterline because users often skim those sections first.

## Metric Direction

Interpret metrics by objective and business meaning:

| Metric group | Examples | Interpretation rule |
|---|---|---|
| Efficiency cost | CPC, CPA, CPM | Lower is better, assuming quality and volume are acceptable. |
| Conversion outcome | Conversions, CVR | Higher is better for conversion-focused campaigns; do not default to this for Reach. |
| Awareness delivery | Impressions, reach, frequency, CPM | Core for Reach/Brand Awareness; zero conversions should not be the default verdict. |
| Engagement/traffic quality | CTR, clicks, landing page views | Higher is usually better for traffic/engagement goals, but clicks are still a scale signal outside traffic goals. |
| Video views | 6s views, completions, CPV | Core for Video Views; conversion is not the default verdict. |
| Scale / spend | Spend, impressions | Higher means more delivery or investment, not automatically better. |

For Spend, use neutral language such as "higher/lower than median" rather than
"better/worse." For Conversion, prioritize it in conversion-focused conclusions because it is a
core advertising outcome.

## Objective-Specific Verdicts

Use the resolved objective to decide what "good" means:

| Objective | Default verdict language |
|---|---|
| Conversion | CPA/CVR/conversion volume versus comparable conversion objects. |
| App | Install or conversion volume and cost per install/conversion; CTR is supporting. |
| Lead | Form/sales lead volume and CPL; CTR/CPC explain upstream traffic. |
| Reach | CPM and exposure/reach/frequency. Say 0 conversion is not enough to call it poor. |
| Traffic | CPC, CTR, clicks, and landing page views. CPA is post-hoc only. |
| Video | 6s views, completions, video plays, and CPV. |
| Product Sales | Purchases/payments, cost per purchase, and ROAS when supported. |

## Insights

Insights connect multiple facts, but must stay within the data actually pulled.

Good:

```text
- The target is buying clicks efficiently relative to account history, but the low CVR suggests the
  post-click path or audience intent may be weaker than usual.
```

Avoid:

```text
- The creative is bad.
- Increase budget by 20%.
- The landing page is broken.
```

Those may be hypotheses, not conclusions, unless supporting data was pulled.

## Suggested Next Steps

Suggestions should be conditional and metric-aware.

| Observed pattern | Safe next step |
|---|---|
| CPC/CPM better than benchmark, CTR below benchmark | Inspect creative hook/audience relevance; optionally pull ad-level breakdown |
| CTR strong, CVR weak | Check conversion event, landing page, audience intent, or pull downstream conversion report |
| Spend higher than median, efficiency worse than median | Review pacing and targeting; route to budget optimization only if the user asks for action |
| High volume, small benchmark sample | Extend benchmark window or switch to a coarser grain |
| CPA unavailable due to zero conversions | Report zero-conversion share; avoid CPA verdict |
| Requested metric unsupported | Explain the unsupported metric and offer supported core metrics or endpoint investigation |
| Object has no analysis data | Offer a longer analysis window or choose a cost-active object |
| High CVR but tiny sample | Put it in directional observations, not the main recommendation bucket |
| Low CPA and high scale but average CVR | Label it as a cost-efficient scale candidate, not a high-CVR candidate |
| Strong candidate is disabled | Mark status risk and suggest checking stop reason before reuse or scaling |
| Mixed objective account | Split into objective buckets; avoid one blended CPA/CVR verdict |
| Brand/Reach campaign has zero conversions | Explain objective mismatch and evaluate CPM/exposure/reach instead |
| Smart+ material enrichment unavailable | Keep the Ad-level benchmark and avoid material-level claims |

Do not give write-action recommendations such as pausing, increasing budget, or editing bids as
direct instructions from this skill. Phrase them as "consider reviewing" or route to
`tt4b-optimize-budget` / `tt4b-manage-campaign` if the user asks to act.

## Sample Caveat Language

Keep confidence as an internal calculation field, but translate it into a sample caveat in the
narrative. Do not put `high`, `medium`, `low`, or `unavailable` in the human-facing metric table
unless the user explicitly asks for diagnostic details.

## Goal Sensitivity

If the user has not stated a goal, use `objective_type` as the goal proxy. Ask only when objective
cannot be resolved and the conclusion would change materially.

- Conversion efficiency goal: prioritize CPA, CVR, CPC, conversion volume.
- Traffic goal: prioritize CPC, CTR, clicks, CPM.
- Awareness/video goal: prioritize CPM, impressions, video views, completion metrics.
- Engagement goal: prioritize CTR plus profile visits, follows, likes, comments, shares.

Spend is not inherently good or bad. Interpret spend only with efficiency, delivery, and objective
context.

## Creative/Material Winner Language

For "best creative/material" requests, default to Ad-level creative/ad benchmark with three labels
instead of a single ranking:

- Scale champion: the ad/creative with the most primary outcomes. Good for contribution, not
  automatically good for efficiency.
- Efficiency champion: the non-tiny-sample ad/creative with the best CPA/CPV/CPL.
- Overall winner: enough primary outcomes and efficiency clearly better than same-objective
  benchmark.

If optional Smart+ material enrichment is available, use it only to explain what contributed
behind the Ad-level result.

Keep tiny samples out of the main winners. Put them in directional observations with the sample
caveat.
