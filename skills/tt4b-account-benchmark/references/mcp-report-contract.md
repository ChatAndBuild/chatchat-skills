# TT4B Account Benchmark MCP Contract

This contract is host-neutral. Claude, Codex, or another agent host may expose the MCP tools with
different call syntax, but the logical tool calls and response expectations stay the same.

## Required MCP Backend

Use the participating-party TikTok Ads MCP backend only. Depending on the host, it may be exposed
as direct `tt-ads` tools or through the kit dispatcher `tt-ads-mcp`.

Scripts in this skill must never call TikTok or any external network directly; all external
reporting data comes from the MCP backend.

## Required Logical Tools

| Logical call | MCP tool | Purpose |
|---|---|---|
| Advertiser metadata | `advertiser_info_get` | Resolve account name, currency, timezone, and status |
| Analysis report | `report_integrated_get` | Fetch one target Campaign, Ad Group, or Ad |
| Benchmark report | `report_integrated_get` | Fetch same-grain account benchmark pool |

In dispatcher-only kit environments, inspect schemas with `tool_get` and call the equivalent
reporting tool through `tool_execute`; this is commonly `Run_a_synchronous_report` for BASIC
reporting. Keep the logical params and response expectations in this contract unchanged.

`report_ad_benchmark_get` is optional enrichment only. It is not the primary path because observed
responses can be empty and delayed.

Optional Smart+ material enrichment:

| Logical call | MCP tool | Purpose |
|---|---|---|
| Smart+ material enrichment | `smart_plus_material_report_overview_run` through native tool or `tool_execute` | Fetch `main_material_id`-level Smart+ creative/material context behind Ad-level results |

If the host exposes a dispatcher only, use `tool_get` to inspect the exact schema for
`smart_plus_material_report_overview_run`, then call it through `tool_execute`.

Optional read-only status enrichment:

| Logical call | MCP tool | Purpose |
|---|---|---|
| Manual Campaign/Ad Group/Ad list/status | `Get_campaigns` / `Get_ad_groups` / `Get_ads` through dispatcher when available | Read current status, parent linkage, type, and budget context |
| Smart+ Campaign/Ad Group/Ad list/status | `Get_Upgraded_Smart_Campaigns` / `Get_Upgraded_Smart_Ad_Groups` / `Get_Upgraded_Smart_Ads` when available | Read current Smart+ object status and parent linkage |

Use these only as read/list lookups. Do not call `Update_*` status tools from this benchmark
skill. If only write/update status tools are exposed, do not use them for lookup; report status as
unavailable from the current safe read toolset.

## Preflight And Auth

Before report pulls, confirm the host can access the logical TikTok Ads MCP backend and these
reporting capabilities:

- `advertiser_info_get`
- `report_integrated_get`

If the host reports an OAuth/auth problem, stop before making report requests. Common auth signals
include:

```text
invalid_token
invalid access token
AuthRequired
unauthorized
401
```

In Codex, the normal recovery is:

```bash
codex mcp login tt-ads
```

If the API returns advertiser-level permission errors, surface the raw `code`, `message`, and
request id. Do not retry with another advertiser unless the user chooses one or a verified account
picker resolves the context.

If `auth_advertiser_get` returns an empty list, ask for an `advertiser_id` and proceed with that ID
when provided. Empty discovery is not the same as proof that the advertiser is inaccessible.

If BC lookup times out but an `advertiser_id` is known, skip BC metadata and try the read-only
report path directly.

Retry transient MCP/TikTok network or timeout errors once. Do not retry permission errors,
authentication errors, or invalid-parameter 4xx responses unchanged.

## Entity Mapping

| Entity | `data_level` | Dimension | Filter field | Name metric |
|---|---|---|---|---|
| Campaign | `AUCTION_CAMPAIGN` | `campaign_id` | `campaign_ids` | `campaign_name` |
| Ad Group | `AUCTION_ADGROUP` | `adgroup_id` | `adgroup_ids` | `adgroup_name` |
| Ad | `AUCTION_AD` | `ad_id` | `ad_ids` | `ad_name` |

Request the name metric by default for both analysis and benchmark reports. If the name metric is
not supported by the endpoint or causes a field error, drop it once and retry, but preserve that
fact for output so the response can show `Unknown name` with a disclosure. Do not replace names
with inferred labels.

The filter field is intentionally plural. Do not substitute the dimension name for the filter
field.

For creative/ad discovery, `ad_id` is the benchmark unit. Do not aggregate benchmark conclusions by
`ad_name`. If the report path or adjacent tools expose `creative_id`, `material_id`, `video_id`, or
status fields, include them as context, but keep the benchmark grain at Ad unless a verified
asset-level report path is added.

## Ads Manager Deep Links

Reporting entity mapping and Ads Manager URL filters are intentionally different. Use reporting
IDs for benchmark computation, then build user-facing object links with this platform mapping:

| Output grain | Ads Manager route | URL filter field | ID source |
|---|---|---|---|
| Campaign | `/i18n/manage/campaign` | `campaign_ids` | report `campaign_id` |
| AdGroup | `/i18n/manage/adgroup` | `ad_ids` | AdGroup identity: report `adgroup_id`, or `ad_id` only when the MCP names the AdGroup identity that way |
| Ad / Creative | No Ads Manager object link | N/A | Render object name as plain text for both ordinary and Smart+ / virtual rows |

The URL filter field names are Ads Manager UI names, not always reporting API dimension names. For
AdGroup links, keep `filters[0][field]=ad_ids`, but put the selected AdGroup's identity in
`filters[0][in_field_values][0]`. Do not substitute a child Ad ID from an Ad-level row.

For Ad / Creative output, do not build Ads Manager object links. This applies to ordinary Ad rows
and Smart+ / virtual Creative rows. Keep `creative_id`, `virtual_creative_id`, `smart_plus_ad_id`,
`main_material_id`, and `smart_plus_ad_get.creative_list[].ad_material_id` as asset or linkage
context only; do not use them as user-facing link filters.

When link fields are available, every user-visible Campaign / AdGroup reference should render as a
Markdown link whose label is the object name only. Ad / Creative references should render as plain
object names. Do not add a standalone object `ID` column. If a required Campaign / AdGroup link ID
is missing, keep the object name as plain text, mark the output as a partial link state, and name
the missing field.

Build Ads Manager object links from the stable campaign-list template. Keep
`navigate_from=campaignList`, keep the standard `columns` list used by the bundled compute
scripts, set `aadvid` to the active advertiser, set `st` and `et` to the actual benchmark request
window, and then set the grain-specific filter. Do not add `relative_time`, `sort_state`, or
`sort_order`; explicit dates are the source of truth for the link window.

Do not simplify the filter into top-level query parameters like `campaign_ids=<id>` or
`ad_ids=<id>`. Ads Manager expects the sidebar filter shape for linked Campaign / AdGroup output:
`filters[0][field]=<campaign_ids|ad_ids>`,
`filters[0][filter_type]=0`, `filters[0][in_field_values][0]=<id>`, and
`filters[0][source]=sidebar`. Links missing this filter shape can render the page without
filtering to the intended object.

For candidate, hot-object, or worth-scaling outputs, attempt status lookup after candidate
selection and before the final verdict. At Ad Group grain, check both `adgroup_id` and parent
`campaign_id` when parent linkage is available. At Ad grain, check Ad, parent Ad Group, and parent
Campaign. If status cannot be retrieved, state the attempted safe-read path and keep the scaling
read conditional.

For Smart+ creative discovery, the main benchmark remains Ad grain. When
`smart_plus_material_report_overview_run` is available, `main_material_id` may be used as an
optional enrichment key to explain material contribution behind Ad-level candidates. Use
`creative_id`, `main_material_name`, and `main_material_type` as context only.

For Smart+ material enrichment, request or retain `main_material_name` and `main_material_type`
when available. If unavailable, do not block the Ad-level benchmark; disclose only when material
context would change the conclusion.

## Objective Fields

Resolve `objective_type` before selecting metrics and benchmark language.

- At Campaign grain, request `objective_type` when supported by the report or retrieve it with an
  adjacent Campaign get endpoint/tool.
- At Ad Group or Ad grain, resolve parent Campaign objective when the report row does not include
  objective.
- If requesting `objective_type` in a report causes a field/metric 400, remove it from the report
  request and use an adjacent object lookup if available.
- If objective remains unavailable, state that objective context was not verified and avoid a hard
  objective-specific verdict.

When the benchmark pool contains multiple objectives, filter or bucket locally by objective before
computing benchmark. The bundled compute script supports this with:

```bash
node scripts/compute-account-benchmark.mjs \
  --analysis raw-analysis.json \
  --benchmark raw-benchmark.json \
  --objective-field objective_type \
  --objective-type WEB_CONVERSIONS
```

## Supported Metrics

Default supported metrics for this BASIC report path:

```text
spend
impressions
clicks
conversion
ctr
cpc
cpm
conversion_rate
cost_per_conversion
video_play_actions
video_watched_2s
video_watched_6s
video_views_p25
video_views_p50
video_views_p75
video_views_p100
profile_visits
follows
likes
comments
shares
```

For user-facing names, aliases, metric directions, and unsupported metric handling, use
`references/metric-catalog.md`.

Do not request commerce or revenue metrics through this contract unless a verified endpoint is
added. Unverified revenue-style fields can return invalid metric errors on the BASIC
`report_integrated_get` path.

If the user asks for unsupported metrics, remove them from the report request, explain the current
contract limitation, and continue with supported metrics only when the remaining metric set still
answers the user question.

If a report returns invalid metric/field errors, degrade the request:

1. Drop the invalid metric or field.
2. Retry once with the reduced metric set.
3. Persist both the error and the successful raw response when the host supports artifacts.
4. Tell the user which metric was unavailable and how the conclusion was adjusted.

## Analysis Report Params

Use this shape, replacing the entity-specific values from the mapping table:

```json
{
  "advertiser_id": "<advertiser_id>",
  "report_type": "BASIC",
  "data_level": "<data_level>",
  "dimensions": ["<dimension>"],
  "metrics": ["<name_metric>", "spend", "impressions", "clicks", "conversion", "ctr", "cpc", "cpm", "conversion_rate", "cost_per_conversion"],
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "filtering": [
    {
      "field_name": "<filter_field>",
      "filter_type": "IN",
      "filter_value": "[\"<entity_id>\"]"
    }
  ],
  "page": 1,
  "page_size": 20,
  "enable_total_metrics": true
}
```

## Benchmark Report Params

Use the same `data_level`, dimension, and metrics as the analysis report. The benchmark report is
not filtered to the target entity, but it must be filtered or bucketed locally to the target
objective before computing objective-specific conclusions.

```json
{
  "advertiser_id": "<advertiser_id>",
  "report_type": "BASIC",
  "data_level": "<data_level>",
  "dimensions": ["<dimension>"],
  "metrics": ["<name_metric>", "spend", "impressions", "clicks", "conversion", "ctr", "cpc", "cpm", "conversion_rate", "cost_per_conversion"],
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "order_field": "spend",
  "order_type": "DESC",
  "page": 1,
  "page_size": 1000,
  "enable_total_metrics": true
}
```

Always pass `page`. If `data.page_info.total_number > 0` but `data.list` is empty, treat it as a
pagination/response-shape problem and retry with explicit pagination before computing benchmark
results.

Do not pass `order_field=stat_time_day`; that field is not supported for sorting in observed
report calls. For day trend requests, omit `order_field` or order by a supported metric.

## Pagination

`page_size` should be at most 1000. Page through all benchmark rows needed for the selected account
and grain. If the account has very large Ad volume, batch by Campaign or Ad Group filters rather
than merging grains.

For Ad-level benchmark pools, do not assume the first page is representative. Page through all
needed rows, or when sorted by spend descending, continue at least until the fetched rows show no
additional cost-active Ads. API-side `spend` filters are not supported on this report path, so
cost-active filtering must happen locally after retrieval.

## Smart+ Material Enrichment Expectations

When using `smart_plus_material_report_overview_run`:

- Use the same date window as the benchmark request.
- Use objective-aware metrics where supported.
- Use endpoint-specific keys from `references/metric-catalog.md`; for example Smart+ material CVR
  may be `conversion_rate_v2`, not BASIC `conversion_rate`.
- Aggregate rows by `main_material_id`.
- Sum additive metrics locally and derive CPA/CVR/CTR/CPM after aggregation.
- If the tool is unavailable or returns a permission/unsupported error, keep the Ad-level benchmark
  as the main result and avoid material-level claims.

## Expected Response Shape

The compute script accepts:

- raw TikTok response with `data.list`
- raw report data object with `list`
- MCP content block containing a JSON string

API errors should be surfaced with `code`, `message`, and `request_id`. Do not hide MCP/API errors
behind host runner errors.

## Raw Response Persistence

When the host supports file artifacts or run storage, persist raw responses immediately after each
successful MCP call:

```text
raw-advertiser.json
raw-analysis.json
raw-benchmark.json
raw-smart-plus-material.json
```

These raw files are the boundary between API retrieval and local deterministic computation. If the
agent stalls while writing the final answer, use the persisted raw responses to compute or resume.
If a raw response is missing, do not substitute sample, synthetic, or example data.
