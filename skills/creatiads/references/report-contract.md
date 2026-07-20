# Report Contract

Use this contract for substantive analysis and client-facing reports.

## Report Request

Normalize vague report requests into a compact request before pulling data or writing HTML:

```json
{
  "platform": "tiktok",
  "account_or_advertiser_id": "required unless the user only asks for a template",
  "period": "daily | weekly | custom",
  "depth": "fast | standard | full | deep",
  "timezone": "account timezone when known",
  "since": "YYYY-MM-DD for custom",
  "until": "YYYY-MM-DD for custom",
  "comparison_since": "YYYY-MM-DD when available",
  "comparison_until": "YYYY-MM-DD when available",
  "known_user_type": "optional user-confirmed advertiser type",
  "output": "html"
}
```

`period` controls the date window. `depth` controls data completeness and latency. Never use depth names to mean
daily or weekly cadence.

## Pre-Report Gate

Before a formal report:

1. Ensure the platform MCP is initialized and authorized.
2. Ask for account or advertiser IDs if missing.
3. If user type is missing, classify it from MCP evidence and write `user_type.json` before metric preset,
   probes, analysis, or HTML.
4. Use sampling only when the user explicitly approves it.
5. Decide whether the report is single-period or period-over-period before writing conclusions.
6. Record attribution, modeled-data, SKAN/SAN, W2A redirect, or missing first-party truth limits up front.

## Run Directory

Materialize report data under:

```text
build/creatiads_runs/<platform>_<account_or_advertiser>_<period>_<depth>_<until>/
```

## Required Files

- `manifest.json`: scope, period, depth, MCP server names, tools used, coverage, degraded sources, partial sources, and timestamps.
- `user_type.json`: resolved advertiser/user type, confidence, evidence, and metric preset implication.
- `sources/*.json`: raw or lightly normalized MCP source payloads.
- `analysis_brief.json`: advertiser type, metric set, evidence, findings, risks, and next actions.
- `validation_summary.json`: row counts, numeric field checks, preview coverage, comparison eligibility, and degraded source summary.
- `report_audit.json`: output from `scripts/audit_creatiads_report.py`.
- `report.html`: required only for formal reports.

If the report uses CSV, Excel, CRM, warehouse, order, lead-quality, margin, cohort, LTV, retention, or other
external business data, keep normalized intermediate files in the run directory and cite each file's provenance.

## Manifest Fields

Include:

- `platform`
- `account_or_advertiser_id`
- `period`
- `depth`
- `since`
- `until`
- `comparison_since`
- `comparison_until`
- `mcp_servers`
- `tools_used`
- `coverage`
- `degraded_sources`
- `partial_sources`
- `privacy_redactions`
- `source_files`
- `not_queried_sources`
- `comparison_eligible`
- `validation_status`

Each source listed in `source_files` must exist relative to the run directory. When a source is not queried because
it is outside the selected scope, list it under `not_applicable_sources` rather than leaving it absent or ambiguous.

## Coverage Header

Every formal report must make the handoff context visible near the top of the HTML:

```text
Scope: platform, account/ad account/advertiser IDs, date range, timezone when known
User type: label, confidence, source
Classification source: user-provided | MCP evidence | unavailable
Metric set: preset name or custom set
Coverage: full | batch | partial | sampled | degraded | failed_with_reason
Limits: platform-reported data only unless external business data was provided
```

For batch or multi-account reports, also include profile, fallback count/reasons, and whether metrics are comparable
across advertiser types.

## Report Shape

Formal reports should include:

- scope and data quality
- KPI snapshot
- trend and anomaly summary
- campaign/ad group/ad drivers
- creative and asset observations where available
- audience, placement, geo, or device diagnostics where available
- landing page, app path, catalog, dataset, or pixel health where available
- opportunity and blocking-error summary
- next actions with approval requirements

Use this default section order:

1. Scope and KPI summary.
2. Executive summary.
3. Recommended actions.
4. Campaign, ad group, and ad drivers.
5. Creative/ad table with preview contract.
6. Landing page, app, W2A, SKU, catalog, or shop path.
7. Audience, placement, device, and geo.
8. Measurement risks and data gaps.
9. Data quality and provenance.

## TikTok Report Requirements

For TikTok formal reports, read [tiktok-report-runner](tiktok-report-runner.md) first and include these source families when required by depth:

- current and previous KPI rows
- campaign, ad group, ad, Smart+, and creative rows
- advertiser type and metric preset
- metric probe when key core or vertical fields are absent
- audience breakdowns for country, age/gender, placement, and device when supported
- landing, SKU, app, W2A, catalog, and shop path evidence
- targeted activity/changelog context for top changed objects
- creative retention and preview enrichment for final report rows
- blocking errors, review status, and degraded source notes

Daily reports must explain anomalies and same-day priority actions. Weekly reports must include period-over-period drivers and next-week action plans.

## TikTok GMV Max Reports

For GMV Max / TikTok Shop / Product GMV Max report requests, read [gmv-max-reporting](gmv-max-reporting.md)
and set the report mode to `gmv_max`. These reports use `/report/gmv_max/get/` and GMV Max store/campaign/product
sources as the primary data plane. Regular auction campaign, ad group, ad, audience, and changelog sources are
not required unless the user explicitly asks for mixed auction + GMV Max coverage.

GMV Max reports must include:

- GMV Max stores and availability
- Product GMV Max campaign discovery, and Live GMV Max discovery when in scope
- account, campaign, product/item-group, creative/item, and duration GMV Max report rows
- campaign item previews and store product enrichment
- Product Card / All Products aggregate for `item_id=-1`
- Product / Item Group table and Creative / Item table
- preview/image caching notes and data-quality reconciliation

Do not mark a GMV Max-first report degraded because regular auction campaign/adgroup/ad/activity sources are
empty. Degrade only when required GMV Max sources are missing, unsupported, permission-denied, partial without
reconciliation, or failed without a structured fallback.

## Daily Pulse Shape

Daily pulse reports should stay fast and operational. Use low-request pulls, do not trigger full landing or full
metric probes unless the user asks for deep diagnosis, and include:

- status: `normal`, `watch`, or `urgent`
- scope, user type, classification source, date, and coverage state
- KPI snapshot: spend, impressions, clicks, CTR, CPC, CPM, result/conversion, cost per result/conversion, and the
  active vertical metric when known
- anomaly object list and changed-object evidence
- delivery blockers, pacing, review, status, budget, or tracking notes
- same-day priority actions
- no-action areas when important
- data gaps and degraded sources

## Weekly Report Shape

Weekly reports should use current 7 complete days versus previous 7 complete days unless the user gives explicit
dates. Include:

- scope, user type, classification source, current and comparison windows, and coverage state
- executive summary
- KPI change table with spend, clicks, result/conversion, cost per result/conversion, and the active vertical metric
- driver table with evidence, impact, and confidence
- winners, watchlist, and bleeders
- creative and audience notes
- landing, app, W2A, catalog, shop, or measurement notes where available
- next-week action plan with approval requirements
- data gaps and caveats

## Chat Response

Do not paste full reports in chat. Return a concise result summary:

- `html_path`: primary formal artifact
- `run_dir`: source run directory
- `manifest_path`: manifest location
- `period`: current and comparison windows
- `depth`: `fast`, `standard`, `full`, or `deep`
- `coverage`: full, batch, partial, sampled, degraded, or failed with reason
- `topline`: spend, result/conversion, cost per result/conversion, revenue/value/ROAS when available
- `degraded_sources`: failed, partial, permission, rate-limit, unsupported, or supported-empty notes
- `verification`: audit status and remaining caveats

## HTML Rendering Rules

Every formal HTML report must include CSS equivalent to:

```css
.table-wrap { overflow:auto; max-width:100%; }
table { table-layout:fixed; width:100%; }
th, td { overflow-wrap:anywhere; word-break:break-word; }
.table-wrap a { overflow-wrap:anywhere; word-break:break-all; }
```

Creative, ad, video, image, or asset rows must include:

- `Preview`: inline image when an MCP source returns a usable thumbnail, cover, or preview image.
- `Preview action`: hover, focus, or click target when an MCP source returns a preview, playable, video, image, Spark post, or equivalent inspection URL.
- `Unavailable`: explicit value when preview evidence cannot be fetched.

For TikTok, follow [tiktok-creative-preview-resolution](tiktok-creative-preview-resolution.md). Do not count a Spark post ID, asset ID, creative ID, or media ID as `with_preview` unless a safe URL or inline image field is also returned.

Do not drop a report row because preview enrichment fails.

## Validation

Before returning a formal report:

1. Write `validation_summary.json`.
2. Run `scripts/audit_creatiads_report.py`.
3. Write `report_audit.json`.
4. Fix required audit failures.
5. Validate that all manifest source-file references exist and parse.
6. Validate that current and comparison windows have rows before writing period-over-period conclusions.
7. If a required source is impossible to fetch, mark the report `passed_with_degradation` only when the missing source is documented in `manifest.json`, `validation_summary.json`, and the HTML data-quality section.

Use [report-validation](report-validation.md) for the exact validation behavior.

## External Business Data

When the user provides CSV, Excel, exported warehouse data, CRM data, order data, lead quality, margin, retention, cohort, LTV, or first-party conversion truth:

- Keep normalized intermediate files in the run directory.
- Cite provenance in `manifest.json` and the HTML data-quality section.
- Join platform data to external data only on explicit keys or clearly documented matching rules.
- Label first-party metrics separately from platform-reported metrics.
- Do not infer profit, incrementality, LTV, lead quality, or new-customer rate from platform-only data.

## Data Safety

Do not store:

- tokens
- authorization headers
- OAuth callback secrets
- MCP session metadata
- data for accounts outside the approved scope

Use `partial` when a source is missing but the report can still answer part of the question. Use `degraded` when a requested source failed and the conclusion has lower confidence.

## Creative Preview Embedding

When generating HTML reports, creative preview URLs resolved from MCP tools MUST be
embedded as real HTML elements — not as bare text status labels.

| Resolved Asset | HTML Output |
|---|---|
| `video_cover_url`, `poster_url` | `<img src="{url}" alt="{name}" style="width:100%;aspect-ratio:9/16;object-fit:cover" loading="lazy">` |
| `preview_url` (video) | `<a href="{url}" target="_blank">▶ Play</a>` |
| `image_url` (carousel/static) | `<img src="{url}" alt="{name}" loading="lazy">` |
| `spark_post_url` | `<a href="{url}" target="_blank">View on TikTok</a>` |

**Pre-completion check**: Before returning a report, verify that the HTML contains at least one
`<img>` tag in the creative preview section. A report whose preview section has zero embedded
images is incomplete — the data was fetched but not rendered. See
[tiktok-creative-preview-resolution](tiktok-creative-preview-resolution.md) for the resolution
playbook.

**Tool dispatch for previews**: `file_image_ad_info_get`, `file_video_ad_info_get`, and
`tt_video_list_get` are L1 dispatcher-only tools. Call them via
`tool_execute(tool_name="ToolName", params={{...}})`. Do not skip these tools because they
aren't L0 direct — the L1 dispatcher is the primary path.
