# TikTok Report Runner

Use this reference for Daily Pulse, Weekly Report, custom TikTok reviews, and client-facing TikTok HTML reports.

## Inputs

Required:

- `advertiser_id`
- `period`: `daily`, `weekly`, or `custom`
- `depth`: `quick`, `fast`, `standard`, `full`, or `deep` (`quick` aliases to `fast`)

For `custom`, require:

- `since`
- `until`

Recommended:

- account timezone
- known advertiser type
- primary business goal
- whether W2A/app redirects are expected

## Fresh Pull Gate

Do not treat an existing `build/creatiads_runs/...` directory as a completed run for a new user request.

Run MCP pulls again when any of these are true:

- the user asks to run or rerun a report;
- the skill, MCP mapping, preview resolution, validation, or report contract changed since the artifact was created;
- the user changes account, date range, period, depth, output type, or asks for `full` / `deep`;
- a previous artifact marked a required source as `not_queried`, stale, or inconsistent with current contracts.

If a run directory already exists, overwrite only the report-specific artifacts for the same scope or create a
timestamped sibling. In either case, set a fresh `generated_at`, record the MCP tools actually called, and keep
old artifacts out of the final answer unless they are explicitly being compared.

## Date Windows

- `daily`: yesterday in account timezone, compared with the day before.
- `weekly`: last 7 complete days, compared with the previous 7 complete days.
- `custom`: use user-provided dates; compare only when equal-length previous dates are supplied or can be safely inferred.

## Depth

| Depth | Sources |
| --- | --- |
| `quick` / `fast` | current advertiser/campaign/ad/ad_v2, previous advertiser/campaign, country audience, landing fallback, targeted activity context |
| `standard` | quick plus current/previous ad groups and ads, age/gender + placement audience, apps, top structure, creative previews, creative retention, targeted activity factors |
| `full` | standard plus device audience, metric probe, higher insight/landing limits, top 60 structure |
| `deep` | full plus all-structure pagination, advertiser-wide changelog, broad audit/debug evidence |

## Candidate Pool And Final Row Selection

For formal TikTok reports, ranking starts only after user type and metric preset are complete:

1. Pull minimal current-window classification seed rows and app/catalog/shop/Smart+ evidence.
2. Write `user_type.json`.
3. Write `metric_preset.json` from that exact `user_type.json`.
4. Pull current-window formal report rows for each report level when the MCP route supports pagination.
   These are full candidate pools, not top-row samples. Use a large enough `page_size` or fetch and merge
   all pages so the source `row_count` matches TikTok `page_info.total_number`:
   - advertiser/account one-row total (`current_advertiser_insights.json`)
   - campaigns
   - ad groups
   - ads
   - Smart+ or upgraded Smart+ ad identities when present
5. Pull the same levels for the comparison window with the aligned preset metric set, including
   `previous_advertiser_insights.json`.
6. Rank candidate pools by spend first, then result/conversion, value/ROAS when active, CPA/CVR, and anomaly or
   delivery-stop signals.
7. Select the final HTML rows from those ranked pools:
   - top campaigns for driver sections
   - top ad groups for bottleneck and budget sections
   - top ads/creatives for creative, fatigue, preview, and URL/path sections
8. Only after final HTML ad/creative rows are selected, run targeted enrichment for previews, media info, Spark or
   identity post info, creative retention, landing/app/SKU/path aggregation, and review/blocking diagnostics.
9. Do not enrich the whole account by default. If a full-account creative or URL scan is explicitly requested, label
   it as exploratory and keep it separate from the normal report path.

Record candidate-pool limits, fetched row counts, final selected row counts, sort keys, and skipped pages in
`manifest.json` and `validation_summary.json`.

The audit must fail if any formal report source is only partially paginated. A response with
`page_info.total_number > row_count` or `page_info.total_page > 1` is not full coverage until
all pages are merged into that source file.

## Runtime Lessons From Real TikTok MCP Full Runs

Treat these as first-class run rules, not optional clean-up:

- For formal KPI sources, the only valid TikTok report interface is direct
  `report_integrated_get`. Do not use L1 dispatcher, direct HTTP, curl, or Motata data for
  `current_*`, `previous_*`, `ad_v2`, audience, or metric-probe rows.
- In subagent runs, MCP success and raw-file persistence are separate facts. A subagent can
  call MCP successfully and still fail to write `raw/*.json`. If that happens, recover the
  payload from the subagent session JSONL `mcp_tool_call_end` event and write the raw file
  from the main session.
- Prefer `mcp_tool_call_end.payload.result.Ok.content[0].text` for recovery. Avoid parsing
  `function_call_output` for large report responses because the transcript can be truncated,
  escaped, or otherwise become invalid JSON.
- If an event-log payload shows `page_info.total_number` and a complete row list, that event
  is acceptable audit evidence for the raw source even when the subagent final message says
  it could not write files.
- Run `python3 creatiads/scripts/recover_subagent_mcp_payloads.py --run-dir <run_dir>` before
  manual session-log recovery. It matches `mcp_tool_call_end` events to `mcp_tasks.jsonl` and
  writes missing `raw/*.json` files automatically.
- After a native MCP/subagent batch completes, prefer
  `python3 creatiads/scripts/finalize_workflow_run.py --run-dir <run_dir> ...` over hand-running
  recovery, `workflow_runner.py`, audit, and timing summary steps. The finalizer is local-only:
  it never calls TikTok MCP.
- Spawn from the generated `subagent_prompts/*.md` files when available. They already contain
  the direct-report boundary, output paths, and compact return contract.
- When event-log recovery is unavailable, split large report pulls into deterministic page
  ranges and ask each subagent to write page files immediately. Keep the page size small
  enough to avoid transcript breakage: use about 20 rows for campaign/adgroup and 10 rows
  for ad-level payloads with many attributes.
- Do not wait indefinitely for one shard. If a shard has made MCP calls, inspect its session
  log, recover completed pages, then relaunch only the missing page range or source.
- For L1-only enrichment, verify exact tool names with `tool_list` and `tool_get` before
  executing. If the current MCP server does not expose changelog/activity-log tools, write
  `activity_changelog` as `structured_unavailable` with the attempted tool list and exact
  unknown-tool errors.
- A report is not `full` while `activities`, `creative_previews`, `audience_breakdowns`, or `landing_app_paths`
  remain `not_queried`. Query them, then record `ok`, `partial`, `supported_empty`, `permission_denied`, or
  `unsupported` according to the actual MCP response.
- Generate `user_type.json` before metric preset, probes, analysis, or HTML every time, even when a previous run
  directory exists.
- Do not stop at insight reports for creative tables. After selecting final ad rows, call ad detail routes to get
  media, identity, destination, and promoted-object references, then run media/post enrichment.
- For targeted preview enrichment, run
  `python3 creatiads/scripts/prepare_preview_mcp_calls.py --run-dir <run_dir> --advertiser-id <id> --source-id <source>`
  after ad detail sources exist. Execute the concrete calls it returns rather than guessing placeholder values
  from `mcp_tasks.jsonl`.
- For Spark post previews, use `tt_video_list_get` with `item_types: ["VIDEO", "CAROUSEL"]`,
  `page`, and `page_size`; use exact `keyword=<item_id>` lookups for unresolved item IDs. Do not use legacy
  `item_type` / `count`.
- Do not let one permission-denied media ID fail the whole preview block. Record the failed ID, retry the batch
  without it, and mark the affected rows `permission_denied` or `asset_reference`.
- Upgraded Smart+ objects can reject regular ad/ad group review-info routes. Record those routes as `unsupported`
  and use Smart+ review routes when their ID schema matches. If Smart+ review still rejects the IDs, keep status,
  changelog, and object-detail evidence as `partial`; do not fake blocking errors.

## Mandatory Execution Order

Mirror the previous first-class TikTok report runner data flow, replacing each data source with MCP calls.
Do not write `analysis_brief.json` or `report.html` until this sequence has completed or each failed source is
explicitly marked with a structured status.

1. `ensure_mcp_ready` for `tiktok-mcp`.
2. Resolve scope, account timezone when available, current window, and comparison window.
3. Pull account or advertiser details.
4. Pull minimal classification seed sources for the requested advertiser and current window:
   - use advertiser, campaign, ad group, ad, Smart+, app, landing, catalog/shop, identity, and destination evidence;
   - classify from current top-spend evidence before choosing vertical sections;
   - record confidence, evidence, skipped URL/app probe counts, and data gaps.
5. Write `user_type.json`.
6. Resolve and write `metric_preset.json` from `user_type.json`; run `metric_probe.json` before analysis when core, value,
   vertical, or attribution metrics are uncertain.
7. Pull current insight candidate pools in this order: advertiser/account daily, campaign, ad group, ad, then ad_v2
   or Smart+ compatible ad identity rows for landing/asset analysis. Use up to 3000 rows per level when pagination
   is supported.
8. Pull previous-period candidate pools using the same levels, row limits, and metric set before calculating deltas.
9. Pull audience breakdowns required by depth: country for quick/fast; country, age/gender,
   and placement for standard; add device for full/deep.
10. Pull landing/app/SKU/path evidence from report destination attributes first, then ad detail, ad group
    detail, Smart+ ad detail, app, catalog/shop, identity, and Spark evidence as needed.
11. Pull top-object structure details for campaign, ad group, ad, and Smart+ objects.
12. Select final report ad/creative rows from the ranked candidate pools, then run targeted creative retention,
    preview, and URL/path enrichment only for those rows.
13. Pull targeted activities/changelog for top campaign/ad group/ad objects; use create/check/download task
    phases when exposed by MCP.
14. Build activity-targeted insights, daily breakdown, and ranked activity factors when activity rows exist.
15. Write manifest, validation summary, analysis brief, HTML, then run the audit script.

If a step cannot run because the MCP route is absent, permission is missing, or the route rejects the field
combination, keep the step in the manifest with `structured_unavailable`, `permission_denied`, `unsupported`,
`rate_limited`, `supported_empty`, `partial`, or `degraded`. Do not silently skip it.

## TikTok Report Field And Dimension Probing

TikTok report routes can reject valid-looking aliases or dimensions. Probe and retry instead of dropping the
source:

- Use `conversion`, not `conversions`, when the synchronous report rejects `conversions`.
- For audience dimensions, try the most specific compatible report type:
  - `country_code` can work under `BASIC`.
  - `age` + `gender`, `placement`, and `platform` may require `report_type: AUDIENCE` after `BASIC` rejects the
    dimension.
- Record rejected metric and dimension attempts in the source artifact as `unsupported_attempts` or
  `report_type_attempts`.
- Keep current and previous metric sets aligned after probing. If a metric is removed from current, remove it from
  previous too before calculating deltas.

## TikTok Depth Source Requirements

For the selected depth, the following sources must be queried or explicitly classified:

| Source | Required MCP path | Depth | Acceptable final status |
| --- | --- | --- | --- |
| Audience country | `report_integrated_get` with `country_code` | quick/standard/full/deep | `ok`, `supported_empty`, `unsupported`, `permission_denied` |
| Audience age/gender | `report_integrated_get` with `report_type: AUDIENCE` when needed | standard/full/deep | `ok`, `supported_empty`, `unsupported`, `permission_denied` |
| Audience placement | `report_integrated_get` with `report_type: AUDIENCE` when needed | standard/full/deep | `ok`, `supported_empty`, `unsupported`, `permission_denied` |
| Audience device/platform | `report_integrated_get` with `report_type: AUDIENCE` when needed | full/deep | `ok`, `supported_empty`, `unsupported`, `permission_denied` |
| Ad details | `ad_get` for final/top ad rows | standard/full/deep | `ok`, `partial`, `unsupported`, `permission_denied` |
| Ad group details | `adgroup_get` for final/top ad group rows | standard/full/deep | `ok`, `partial`, `unsupported`, `permission_denied` |
| Landing/app paths | Report destination fields plus `ad_get` and `adgroup_get` | quick/standard/full/deep | `ok`, `partial`, `supported_empty`, `unsupported` |
| Creative preview | `ad_get` plus image/video/Spark/identity enrichment | standard/full/deep | `ok`, `partial`, `supported_empty`, `permission_denied` |
| Creative retention | Ad-level report with video play and quartile metrics | standard/full/deep | `ok`, `supported_empty`, `unsupported` |
| Activities | Changelog create/check/download for targeted objects; advertiser-wide at deep | quick/standard/full/deep | `ok`, `supported_empty`, `unsupported`, `structured_unavailable`, `permission_denied` |
| Blocking errors | Review/status routes plus object detail | deep | `ok`, `partial`, `unsupported`, `permission_denied` |

If landing URLs are not returned for selected ads but promoted-object, pixel, app, placement, or destination
evidence is returned, mark `landing_app_paths` as `partial` and explain exactly which evidence exists.

## Agent MCP Prefetch Checklist

Preferred path: run a planner first, then execute only the generated native-MCP tasks:

```bash
python3 creatiads/scripts/plan_full_report.py \
  --advertiser-id <id> --since YYYY-MM-DD --until YYYY-MM-DD \
  --previous-since YYYY-MM-DD --previous-until YYYY-MM-DD \
  --depth full --run-dir <run_dir>
```

For non-report work, use the matching planner (`plan_user_type.py`,
`plan_metric_profile.py`, `plan_performance_diagnosis.py`,
`plan_landing_app_paths.py`, `plan_creative_diagnosis.py`,
`plan_audience_diagnosis.py`, `plan_activity_changelog.py`,
`plan_bottleneck_diagnosis.py`, `plan_budget_recommendation.py`,
`plan_gmv_max_report.py`, `plan_preflight_validate.py`, or
`plan_staged_operations.py`). These planners
write `pull_plan.json`, `mcp_tasks.jsonl`, and `summary.json`. They do not call
MCP, do not run OAuth, and do not use Motata CLI.

The agent must execute `mcp_tasks.jsonl`, write raw responses to `<run_dir>/raw/`,
normalize them into `<run_dir>/sources/`, and validate the state before invoking
`run_report.py --data-dir <run_dir>`. Each source file follows the shape:

```json
{"status": "<status>", "phase": "<bootstrap|classification|preset|report_data|enrichment|analysis>", "rows": [...], "generated_at": "<ISO 8601>"}
```

Allowed statuses: `ok`, `supported_empty`, `unsupported`, `not_queried`,
`permission_denied`, `rate_limited`, `degraded`, `partial`,
`structured_unavailable`, `not_applicable`.

### Resolution Order (every tool call)

1. For formal report rows, call direct `report_integrated_get` and follow the task retry
   ladder only. Do not use L1 dispatcher for KPI report pulls.
2. For non-report tools, try L0 direct (e.g. `mcp__tiktok-mcp__smart_plus_ad_get`).
3. If "unknown tool" or failure, fall back to L1:
   `mcp__tiktok-mcp__tool_execute(tool_name="...", params={...})`.
4. Only if both fail, write the source file with `structured_unavailable`.

### Subagent Runbook

Use this loop whenever `workflow_runner.py` returns `awaiting_mcp` and the selected backend is
`mcp_subagent_executor`:

1. Spawn narrow subagents by shard or by source family. For the first report, spawn only shards
   marked `execution_stage: blocking_before_report`; defer `optional_after_first_report` preview
   and activity-enrichment shards until after the first audited HTML exists or the user requests
   enriched rerender. Give each worker exact task IDs and forbid Motata, direct HTTP, and
   dispatcher use for KPI report pulls.
2. Use generated `subagent_prompts/*.md` files instead of hand-writing long prompts. Launch
   independent formal and audience shards in parallel up to the plan's `max_concurrency`.
3. After every MCP call, the subagent must write the planned raw file and verify it is non-empty
   before starting the next task. If it cannot write/verify, stop that shard and recover.
4. After a short wait window or after a subagent returns, verify files in `<run_dir>/raw/`. If files exist, run
   `workflow_runner.py --quiet` with the full date arguments.
5. If files are missing, run
   `python3 creatiads/scripts/recover_subagent_mcp_payloads.py --run-dir <run_dir>` before
   inspecting session files manually.
6. Write the recovered JSON to the planned `output_raw` path, then rerun `workflow_runner.py`.
7. If a subagent only finished part of a paginated source, merge recovered pages only when all
   pages are present. Otherwise relaunch the missing page range.
8. If a source is absent because the MCP server does not expose that capability, write a
   structured source with `status: structured_unavailable`, `attempts`, `errors`,
   `backend: mcp_subagent_executor`, and a clear message.
9. Close completed subagents after recovery to avoid stale concurrent work.

### Standard Depth Checklist

| # | Source File | MCP Tool | Level | Key Params | Normalization |
| --- | --- | --- | --- | --- | --- |
| 1 | `mcp_ready.json` | `tool_list` | L1 | `{}` | `phase: bootstrap` |
| 2 | `current_account.json` | `advertiser_info_get` | L0 | `advertiser_ids: [<id>]` | `phase: bootstrap`; extract name, currency, timezone, industry |
| 3 | `classification_campaigns.json` | `report_integrated_get` | L0 | current window, minimal current metrics | `phase: classification`; names/objectives/spend |
| 4 | `classification_adgroups.json` | `report_integrated_get` | L0 | current window, minimal current metrics | `phase: classification`; promotion/app hints |
| 5 | `classification_ads.json` | `report_integrated_get` | L0 | current window, top spend ads | `phase: classification`; ad names/text/URLs |
| 6 | `classification_ad_v2_insights.json` | `report_integrated_get` | L0 | current window, ad_id_v2 | `phase: classification`; destination/app hints |
| 7 | `smart_plus_ads.json` | `smart_plus_ad_get` | L0 | `advertiser_id`, paginate | `phase: classification`; landing_page_url_list, creative_list, ad_configuration |
| 8 | `app_list.json` | `app_list_get` | L0 | `advertiser_id` | `phase: classification`; app/store evidence |
| 9 | `catalog_list.json` | `catalog_get` | L0 | `bc_id` | `phase: classification`; ecommerce evidence |
| 10 | `shop_list.json` | Shop endpoint | L1 | `advertiser_id` | `phase: classification`; ecommerce evidence or `supported_empty` |
| 11 | `user_type_evidence.json` | Derived locally | Mixed | — | `phase: classification`; app campaign skip and landing evidence |
| 12 | `user_type.json` | Generated by `classify_user_type.py` | — | — | `phase: classification`; 13-class output and derived user type |
| 13 | `metric_preset.json` | Generated by `metric_probe.py` from user_type | — | — | `phase: preset`; includes `source_user_type_hash` |
| 14 | `current_advertiser_insights.json` | `report_integrated_get` | L0 | `data_level: AUCTION_ADVERTISER` | one-row KPI total anchor |
| 15 | `current_campaigns.json` | `report_integrated_get` | L0 | selected preset metrics | `phase: report_data`; merge campaign attributes |
| 16 | `current_adgroups.json` | `report_integrated_get` | L0 | selected preset metrics | `phase: report_data`; merge names |
| 17 | `current_ads.json` | `report_integrated_get` | L0 | selected preset metrics | `phase: report_data`; merge names |
| 18 | `current_ad_v2_insights.json` | `report_integrated_get` | L0 | selected preset metrics + ad_id_v2 | `phase: report_data` |
| 19 | `previous_advertiser_insights.json` | same as #14, previous window | L0 | same accepted metrics | one-row comparison anchor |
| 20 | `previous_campaigns.json` | same as #15, previous window | L0 | same accepted metrics | `phase: report_data` |
| 21 | `previous_adgroups.json` | same as #16, previous window | L0 | same accepted metrics | `phase: report_data` |
| 22 | `previous_ads.json` | same as #17, previous window | L0 | same accepted metrics | `phase: report_data` |
| 23 | `audience_country.json` | `report_integrated_get` | L0 | `dimensions: ["country_code"]` | `phase: enrichment` |
| 24 | `audience_age_gender.json` | `report_integrated_get` | L0 | fallback age/gender dimensions | `phase: enrichment` |
| 25 | `audience_placement.json` | `report_integrated_get` | L0 | fallback placement dimensions | `phase: enrichment` |
| 26 | `apps.json` | Derived locally | — | app/campaign/ad evidence | Motata-like app summary |
| 27 | `campaign_structure.json` | `campaign_get` | L1 | top campaign IDs | top 30 by spend |
| 28 | `adgroup_structure.json` | `adgroup_get` | L1 | top ad group IDs | top 30 by spend |
| 29 | `ad_structure.json` | `ad_get` | L1 | top ad IDs | top 30 by spend |
| 30 | `ad_details_for_enrichment.json` | `ad_get` | L1 | top ad IDs only | `phase: enrichment`; image/video/Spark IDs per selected row |
| 31 | `creative_preview_images.json` | `file_image_ad_info_get` | L1 | image IDs from ad details | `phase: enrichment`; concrete image URLs |
| 32 | `creative_preview_videos.json` | `file_video_ad_info_get` | L1 | video IDs from ad details | `phase: enrichment`; cover and playable URLs |
| 33 | `creative_retention.json` | Derived locally | — | ad rows | fatigue/retention summary |
| 34 | `targeted_creative_retention.json` | Derived locally | — | targeted/final ad rows | targeted retention summary |
| 35 | `landing_app_paths.json` | Derived locally | Mixed | — | `phase: enrichment`; URL/app/SKU aggregation |
| 36 | `activity_changelog.json` | changelog async flow | L1 | top campaign/adgroup/ad object IDs | targeted activity context |
| 37 | `activity_targeted_insights.json` | Derived locally | — | targeted insight rows | affected object context |
| 38 | `activity_daily_breakdown.json` | Derived locally | — | daily targeted rows | before/after context |
| 38 | `activity_factors.json` | Derived locally | — | changelog + daily context | ranked operational drivers |

### Full Depth (add after standard)

| # | Source File | MCP Tool | Level | Key Params | Notes |
| --- | --- | --- | --- | --- | --- |
| F1 | `audience_device.json` | `report_integrated_get` | L0 | `report_type: AUDIENCE`, `dimensions: ["platform"]` | Remove `total_purchase_value` from metrics |
| F2 | `metric_probe_results.json` | `report_integrated_get` per metric group | L0 | One report per group defined by `recommend_metric_groups()`. Do NOT call blindly for every metric | `{group_name: {status, rows}}` per group |
| F3 | top structure limit | `campaign_get` / `adgroup_get` / `ad_get` | L1 | top spend IDs | expand from 30 to 60 |

### Deep Depth (add after full)

| # | Source File | MCP Tool | Level | Notes |
| --- | --- | --- | --- | --- |
| D1 | `activity_changelog.json` | Same as standard/full, advertiser-wide | L1 | No `object_ids` filter; full advertiser scope |
| D1b | `advertiser_level_changelog.json` | Alias of D1 | — | Compatibility source for audits that still read the old filename |
| D2 | `bottleneck_diagnosis.json` | L1 review info APIs (`ad_review_info_get`, `adgroup_review_info_get`) | L1 | Blocking errors, review status, rejection reasons |
| D3 | `ad_review_info.json` | `ad_review_info_get` | L1 | May reject Smart+ ad IDs; mark `unsupported` if so |

### Degradation Handling

For any source where MCP returns an error or empty result:

- **Permission denied** → write `{"status":"permission_denied","error":"<message>"}`
- **Route unavailable** → write `{"status":"unsupported","error":"<message>"}`
- **Rate limited** → write `{"status":"rate_limited","error":"<message>","retry_after":<seconds>}`
- **Empty result (query succeeded, no data)** → write `{"status":"supported_empty","rows":[]}`
- **Partial data (some IDs failed, others succeeded)** → write `{"status":"partial","rows":[...],"failed_ids":[...]}`
- **Not applicable to this account** → write `{"status":"not_applicable","reason":"..."}`
- **Completely unavailable (unsupported TikTok route or runtime)** → write `{"status":"structured_unavailable","reason":"..."}`

Never silently skip a source that the depth contract requires. Always write a file.
Never treat missing source files as zero data.

## Source Plan

Write each source under `sources/*.json` using stable names:

- `account.json`
- `user_type.json`
- `current_account_daily.json`
- `previous_account_daily.json`
- `current_campaigns.json`
- `previous_campaigns.json`
- `current_adgroups.json`
- `previous_adgroups.json`
- `current_ads.json`
- `previous_ads.json`
- `current_ad_v2_insights.json`
- `smart_plus_campaigns.json`
- `smart_plus_ads.json`
- `advertiser_type.json`
- `metric_probe.json`
- `metric_preset.json`
- `audience_country.json`
- `audience_age_gender.json`
- `audience_placement.json`
- `audience_device.json`
- `landing_app_paths.json`
- `creative_retention.json`
- `creative_previews.json`
- `activities.json`
- `activity_targeted_insights.json`
- `activity_daily_breakdown.json`
- `activity_factors.json`
- `blocking_errors.json`
- `degraded_sources.json`
- `validation_summary.json`
- `report_audit.json`

Skip a source only when not needed for the selected depth or when unavailable. Record skipped or failed sources in `manifest.json`.

## Activities And Changelog

Activities are context, not KPI truth.

For `fast`, `standard`, and `full`:

1. Determine top campaigns, ad groups, and ads from insights first.
2. Discover the narrowest activity or change-log MCP route.
3. Pull targeted activity/changelog rows only for those top objects.
4. Limit operation types to create, update, status, budget, bid, audit/review, targeting, and creative changes when supported.
5. If the platform exposes asynchronous change-log tasks, use create, check, and download phases; parse the downloaded rows before analysis.
6. Join high-impact activity rows back to daily performance for the affected top objects when the report explains a sudden change.

For `deep`:

1. A broader advertiser-level changelog is allowed.
2. Summarize high-impact factors only; do not dump raw activity logs into the report.

Activity outputs:

- `activity_targeted_insights`: performance around changed top objects.
- `activity_daily_breakdown`: before/after trend by changed object.
- `activity_factors`: ranked likely operational drivers.

If activity tools are unavailable for a selected depth that requires them, write `structured_unavailable`,
`unsupported`, `permission_denied`, or `supported_empty` rather than replacing activity evidence with guesses.
Use `not_queried` only when activities are outside the selected scope.

When changelog downloads return CSV-like `file_data`, parse it before analysis. Keep the raw downloaded source in
`sources/activities.json`, and produce:

- `activity_targeted_insights.json`: parsed rows joined to top object insight metrics when IDs match.
- `activity_daily_breakdown.json`: change counts by day and operation area.
- `activity_factors.json`: ranked operational drivers such as budget/schedule, on/off status, review status,
  targeting, and settings/name changes.

If an ad-level changelog task returns only headers, record it as `supported_empty` for that object type while still
using ad group or campaign changelog rows if they exist.

## TikTok ID Routing

Respect TikTok report identity splits:

- Use the report layer first to decide whether upgraded Smart+ asset granularity is available. Do not infer only from
  object names.
- `campaign_automation_type` is the primary detection field. Treat both values as upgraded Smart+:
  - `UPGRADED_SMART_PLUS_CREATIVE`
  - `UPGRADED_SMART_PLUS`
- Interpret those values by the report dimension that produced them:
  - `dimensions=["ad_id"]` plus `campaign_automation_type=UPGRADED_SMART_PLUS_CREATIVE` means `ad_id` is a creative
    identity. Use it for creative tables, previews, creative retention, and material performance.
  - `dimensions=["ad_id_v2"]` plus `campaign_automation_type=UPGRADED_SMART_PLUS` means `ad_id_v2` is the
    `smart_plus_ad_id` or asset-group ad identity. Use it for landing URLs, configuration, and asset-level
    aggregation.
- Confirm upgraded Smart+ availability from all three signals:
  - requested dimensions include `ad_id_v2`;
  - `campaign_automation_type` is one of the upgraded Smart+ values;
  - `ad_id_v2` or `smart_plus_ad_id` exists on the row.
- Do not mix `ad_id` and `ad_id_v2` in the same report request unless the MCP tool explicitly documents the
  combination.
- For upgraded Smart+ landing and asset-group analysis, prefer `current_ad_v2_insights.json` from an upgraded Smart+
  compatible report route, then enrich unique Smart+ identities with Smart+ ad detail in batches of at most 50.
- Never request unsupported destination-list fields after the MCP rejects them; retry with a narrower field set and record the rejected field as `unsupported`.

## Creative Path Versus Landing Path

Run these as parallel and complementary paths when upgraded Smart+ evidence exists.

Creative path:

1. Call the report route with `data_level=AUCTION_AD` and `dimensions=["ad_id"]`.
2. Include spend, result/value, video metrics, `campaign_automation_type`, and campaign/ad group/ad attributes.
3. For upgraded Smart+ creative rows, expect `campaign_automation_type=UPGRADED_SMART_PLUS_CREATIVE` and treat
   `ad_id` as the creative identity.
4. Keep this `ad_id` path for creative tables, previews, retention, material diagnosis, and fatigue analysis.
5. After final creative rows are selected, call `ad_get` with `filtering.ad_ids` for only those creative IDs to get
   image IDs, video IDs, Spark item IDs, playable or preview fields, and other creative references.

Landing path:

1. Call the report route separately with `data_level=AUCTION_AD` and `dimensions=["ad_id_v2"]`.
2. Include spend, result/value, `campaign_automation_type`, campaign/ad group attributes, ad name, and destination
   fields such as `ad_url` when the route accepts them.
3. Identify upgraded Smart+ asset rows where `campaign_automation_type=UPGRADED_SMART_PLUS` and `ad_id_v2` is not
   empty.
4. De-duplicate `ad_id_v2` values and treat them as `smart_plus_ad_id` values.
5. Call `smart_plus_ad_get` with `filtering.smart_plus_ad_ids` in batches of at most 50.
6. Extract `landing_page_url_list[0].landing_page_url` and other Smart+ configuration fields, then backfill that URL
   to all spend/creative rows under the same `ad_id_v2`.

This avoids the slow path of mapping hundreds of creative `ad_id` values through regular ad detail before discovering
their Smart+ asset identity. Use the creative path for creative evidence and the landing path for asset-level URL and
configuration evidence.

## Landing Fallback Order

For upgraded Smart+ rows, resolve destination evidence in this order:

1. `ad_url` from the `ad_id_v2` report row.
2. `landing_page_url_list[0].landing_page_url` from `smart_plus_ad_get`.
3. Smart+ `ad_configuration`, deeplink, page, app, catalog, shop, or promoted-object fields from
   `smart_plus_ad_get`.
4. Parent ad group fallback.
5. Campaign or legacy Smart+ campaign fallback only for legacy Smart+ evidence, not as the upgraded Smart+ primary
   path.

For non-upgraded rows, resolve destination evidence in this order:

1. `ad_url` from the `ad_id` report row.
2. `ad_get` by final `ad_id` values.
3. Ad group destination/download URL or ad group detail.
4. Legacy Smart+ campaign detail when the row is legacy Smart+ and no ad/ad group URL exists.

## Regular Versus Smart+ Enrichment Flow

After final rows are selected, split enrichment by row type.

Regular or manual ad rows:

1. Use `ad_id` as the primary identity.
2. Read `ad_get` for final ad rows.
3. Read `adgroup_get` for their parent ad groups.
4. Extract `landing_page_url`, app/pixel/catalog/product references, identity references, image IDs, video IDs,
   Spark post IDs, playable URLs, and accepted preview fields.
5. Resolve media and post evidence with image/video/Spark/identity tools.

Smart+ or upgraded Smart+ rows:

1. Use `ad_id_v2` or `smart_plus_ad_id` as the primary identity. Keep it separate from regular `ad_id` filters.
2. Use Smart+ compatible reports for candidate rows and material diagnostics.
3. Read `smart_plus_ad_get` in batches of at most 50 selected identities.
4. Prefer Smart+ `landing_page_url_list`, `creative_list`, `image_info`, `video_info`, `tiktok_item_id`, and
   material report rows before falling back to parent ad group or campaign detail.
5. Use `smart_plus_material_report_overview_run` and
   `smart_plus_material_report_breakdown_run` for Smart+ material performance diagnostics.

For mixed accounts, preserve both identity systems in the source artifacts and report table. Never use a regular
ad detail route as proof that a Smart+ row has no creative or URL data; mark the regular route `unsupported` for
that object type and continue with Smart+ routes.

## Creative Preview Enrichment

Read [tiktok-creative-preview-resolution](tiktok-creative-preview-resolution.md) before writing `creative_previews.json`.

Do not scan every creative by default.

1. Select final report ad/creative rows from insights first.
2. Enrich only those rows with the exact MCP-supported route set from [tiktok-creative-preview-resolution](tiktok-creative-preview-resolution.md): regular ad detail, upgraded Smart+ ad detail, Smart Creative materials, image search when ID filtering is supported, video info, Spark Ad posts, identity post info, and upgraded Smart+ material reports when needed.
3. Resolve preview evidence in this order: inline image/thumbnail/cover, playable/video/preview URL, Spark post URL, non-URL asset reference.
4. Do not count `asset_reference`, `spark_post_reference`, or `reference_only` as `with_preview`.
5. Inline one preview image per row in HTML when a safe image/thumbnail/cover URL is available.
6. Keep playable/video/preview/Spark URLs as hover/focus/click actions when safe to store.
7. If a confirmed exact MCP route is absent or fails at runtime, mark that source as `structured_unavailable`, `permission_denied`, `rate_limited`, or `partial` according to the error; never replace it with a non-MCP data source.
8. Mark missing previews as `unavailable`, `permission_denied`, `unsupported`, `structured_unavailable`, or `supported_empty`; never drop rows because preview is missing.
9. Store preview coverage in `validation_summary.json`, counting only rows with concrete preview URLs.

After preview enrichment, write supporting raw sources:

- `sources/ad_details_top*.json`
- `sources/media_image_info.json`
- `sources/media_video_info.json`
- `sources/spark_posts.json`
- `sources/creative_previews.json`
- `sources/creative_retention_raw.json` when retention metrics are queried

`creative_previews.json` must contain one row per final report ad row. Missing preview evidence is a row-level
status, not a reason to shrink the table.

## Daily Pulse Output

Return:

- overall status: `normal`, `watch`, or `urgent`
- KPI snapshot
- anomaly object list
- key changes and likely drivers
- spend pacing or delivery stop notes
- same-day priority actions
- degraded sources and caveats

## Weekly Report Output

Return:

- HTML report path
- run directory and manifest path
- KPI summary
- period-over-period changes
- driver table
- winners, watchlist, bleeders
- creative, audience, landing/app, and measurement notes
- next-week action plan
- approval-gated actions
- verification status

## Audit

Before returning a formal report, verify:

- all required files exist or are marked skipped/degraded
- numeric fields parse
- current and comparison windows are equal length before using percentage deltas
- no secrets or MCP session metadata are written
- unsupported, empty, permission, and rate-limit states are distinct
- HTML includes scope, data quality, KPI snapshot, drivers, findings, next actions, and caveats
- `scripts/audit_creatiads_report.py` has produced `report_audit.json`
- `validation_summary.json` has no `not_queried_sources` for a source required by the selected depth unless the
  source was truly not applicable and the manifest explains why.
