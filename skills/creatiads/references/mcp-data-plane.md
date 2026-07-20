# MCP Data Plane

This reference defines how Creatiads talks to platform MCP servers. There are exactly two paths.

## Two-Tier Architecture

### Tier 1: Direct MCP (Agent → MCP Server, no bridge)

The AI agent calls MCP tools natively through its built-in MCP client. No Python script, no bridge, no subprocess.

**Critical: L0 vs L1 tool availability.** Not all endpoints are exposed as L0 (direct-call) tools.
Many core tools — including `ad_get`, `adgroup_get`, `campaign_get`, `file_image_ad_info_get`,
`file_video_ad_info_get`, `tt_video_list_get`, and some changelog/review helpers — may only be
available through the L1 dispatcher via `tool_execute`. When a tool is L1-only and is exposed by
the current server, the agent MUST call `tool_execute(tool_name="ToolName", params={{...}})` to
reach it.

**Dispatch rule:** Try the L0 direct tool name first. If it returns "unknown tool" or
`structured_unavailable`, fall back to `tool_execute` with the L1 tool name. For non-report
enrichment, do not skip a capability because the L0 path is absent. For formal report rows,
`report_integrated_get` is already L0 direct and must not be routed through `tool_execute`.

Use Direct MCP for **every operation that is a single read or write**:

| Capability | Tool Path | Availability |
|---|---|---|
| Initialize MCP | `codex mcp add` / `codex mcp login` | One-time setup |
| List accounts | `advertiser_info_get` | **L0 direct** |
| Discover assets | BC, identity, app, pixel, catalog, creative portfolio, file tools | Mixed — check L0 first |
| Get campaigns (regular) | `tool_execute("campaign_get", ...)` | **L1 dispatcher only** |
| Get campaigns (Smart+) | `smart_plus_campaign_get` | **L0 direct** |
| Get ad groups (regular) | `tool_execute("adgroup_get", ...)` | **L1 dispatcher only** |
| Get ad groups (Smart+) | `smart_plus_adgroup_get` | **L0 direct** |
| Get ads (regular) | `tool_execute("ad_get", ...)` | **L1 dispatcher only** |
| Get ads (Smart+) | `smart_plus_ad_get` | **L0 direct** |
| Get pages | `page_get` | **L0 direct** |
| Get catalogs | `catalog_get` | Mixed — try L0, fall back L1 |
| Create campaign | Smart+ L0 or campaign group L1 | Approval-gated, paused default |
| Create adset/adgroup | Smart+ L0 or adgroup group L1 | Approval-gated, paused default |
| Create ad | Smart+ L0 or ad group L1 | Approval-gated, paused default |
| Update entity | Smart+ L0 or campaign/adgroup/ad L1 | Approval-gated |
| Activate entity | Status tools (L0 Smart+ or L1 regular) | Separate approval from creation |
| Validate creative | Read identity + media info + landing URL → Agent judges | Read-only checks |
| Validate ad link | Read adgroup/ad detail + promoted object deps → Agent judges | Read-only checks |
| Validate promoted object | Read app/pixel/catalog/identity/objective → Agent judges | Read-only checks |
| Get blocking errors | Review info tools, diagnostic tools | Mixed L0/L1 |
| Get insights | `report_integrated_get` | **L0 direct** |
| **Get video info** | `tool_execute("file_video_ad_info_get", ...)` | **⚠ L1 dispatcher only** |
| **Get image info** | `tool_execute("file_image_ad_info_get", ...)` | **⚠ L1 dispatcher only** |
| **Get Spark Ad posts** | `tool_execute("tt_video_list_get", ...)` | **⚠ L1 dispatcher only** |
| Get creative previews | `smart_plus_ad_get` (L0) + `tool_execute("ad_get", ...)` (L1) + `tool_execute("file_image_ad_info_get", ...)` (L1) + `tool_execute("file_video_ad_info_get", ...)` (L1) + `tool_execute("tt_video_list_get", ...)` (L1) | **See playbook below** |
| Probe metrics | Report calls → Agent classifies each metric result | |
| Get dataset/pixel health | Pixel, app, custom conversion, catalog diagnostic tools | Mixed |
| Analyze measurement/attribution | Probe results + SKAN/SAN checks → Agent logic | |
| Plan budget/bid actions | Insights + entity reads → Agent classifies into action bands | |
| **Get activity changelog** | When exposed: `tool_execute("changelog_task_create", ...)` → `tool_execute("changelog_task_check", ...)` → `tool_execute("changelog_task_download", ...)` | **⚠ L1 dispatcher only; verify names first** |
| Media upload | v2 no `new_name` for image/video upload endpoints | **L1 dispatcher only** |
| Identity management | `identity_get` (L0) + `tool_execute` for others | Mixed |
| Targeting | `tool_execute("search_region_get", ...)` etc. | **L1 dispatcher only** |
| Creative portfolios | `tool_execute("creative_portfolio_create", ...)` etc. | **L1 dispatcher only** |
| Catalog management | Catalog, feed, product, product set tools | Mixed L0/L1 |
| Audience management | 42 audience tools | **L1 dispatcher only** |
| BC management | 53 BC tools | **L1 dispatcher only** |
| GMV Max / TikTok Shop | `tool_execute` for all GMV Max tools | **L1 dispatcher only** |

**Rule**: If a non-report L0 tool call returns "unknown tool" or `structured_unavailable`,
immediately retry via `tool_execute(tool_name="ExactL1ToolName", params={{...}})`. Do NOT mark the
capability as unavailable until `tool_list`/`tool_get` discovery and an exact `tool_execute`
attempt have failed. Some server builds omit groups such as changelog/activity-log; record those
as `structured_unavailable` with attempted tools and exact errors. Formal KPI, comparison,
audience, `ad_v2`, and metric-probe report rows use direct `report_integrated_get` only.

### Creative Preview Resolution Playbook

Getting actual image/video URLs for the HTML report requires this exact dispatch sequence:

1. **Uploaded videos** → `tool_execute("file_video_ad_info_get", {{advertiser_id, video_ids}})` → returns `video_cover_url` + `preview_url`
2. **Carousel/uploaded images** → `tool_execute("file_image_ad_info_get", {{advertiser_id, image_ids}})` → returns `image_url`
3. **Spark Ads (TikTok native posts)** → `tool_execute("tt_video_list_get", {{advertiser_id}})` → returns `poster_url` + `preview_url`
4. **Embed in HTML**: Every resolved URL MUST be embedded as `<img src="...">` (cover/poster) or `<a href="...">▶ Play</a>` (preview). Never use bare text labels like "inline_image" — the URL IS the preview.

**IMPORTANT**: None of `file_video_ad_info_get`, `file_image_ad_info_get`, or `tt_video_list_get`
are L0 tools. All three require `tool_execute`. If you call them as L0 and get "no such tool",
that's expected — use the L1 dispatcher.

## Scripts: Compute-Only (Agent Makes All MCP Calls)

Python scripts are pure-compute functions. They accept MCP data as input and produce analysis
artifacts as output. **Scripts never call MCP tools themselves.** The agent is always the MCP client.

| Script | Input | Output |
|---|---|---|
| `classify_user_type.py` | Advertiser info + campaign/ad names + URLs | `user_type.json` |
| `metric_probe.py` | Report rows by metric group | `metric_preset.json`, `metric_probe.json` |
| `creative_enrichment.py` | Ad rows + media info (image/video/Spark URLs) | `creative_previews.json`, `creative_retention.json` |
| `audience_analysis.py` | Audience report rows | Segment-tagged `audience_breakdowns.json` |
| `landing_app_analyzer.py` | Ad URLs, app IDs, Smart+ landing paths | `landing_app_paths.json` |
| `activity_analysis.py` | Changelog CSV from MCP download | `activities.json`, `activity_factors.json` |
| `audit_creatiads_report.py` | Run directory path | `report_audit.json` |

## Data Quality Rules (apply to both tiers)

### Result Status

- `ok`: request succeeded
- `partial`: request succeeded but coverage is incomplete
- `structured_unavailable`: MCP server or tool namespace is not callable
- `unsupported`: the API rejects a field, dimension, endpoint, or combination
- `supported_empty`: API accepts the request but returns no rows
- `permission_denied`: current OAuth user lacks access
- `rate_limited`: retry later
- `degraded`: a required source failed

Reserve `not_queried` only for sources explicitly skipped by user scope.

### Retry Rules

When a TikTok MCP route rejects a field/metric/dimension:

1. Preserve the failed request in the source artifact
2. Retry with narrower accepted field set when the error reveals a viable route
3. Retry success with fewer fields → mark `partial`
4. Route accepts but returns no rows → mark `supported_empty`
5. Single asset ID fails for permission → retry without that ID, mark only that row

### Pagination

- Conservative page size for first runs
- Batch object detail lookups where MCP schema allows ID lists
- Pull account/advertiser totals first, enrich top objects only
- Select top/final objects from insight rows, batch details for those IDs only
- De-duplicate media IDs before calling image/video/post detail tools

### Artifact Discipline

- Write sources under `sources/*.json`
- `manifest.json` lists MCP tools called with coverage status
- `validation_summary.json` distinguishes: partial_sources, degraded_sources, supported_empty_sources, permission_denied_sources, unsupported_sources, not_queried_sources
- Record `generated_at`, `source`, `status`, `attempts`, row counts per source

## Write Gate

Before create, update, activate, delete, share, budget, or status operations:

1. Read the target account and object
2. Validate required linked assets (page, pixel, dataset, catalog, identity, app, product set, creative)
3. Present payload summary, target IDs, risk, and default status
4. Ask for explicit approval
5. Execute only the approved operation

Creation defaults: **paused or disabled**. Activation is always a separate approval step.
