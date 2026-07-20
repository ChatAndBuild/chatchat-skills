# TikTok Operation Map

Use this map after MCP initialization for TikTok tasks. It translates user-facing operating needs into MCP-first adapter behavior and focuses on ads operations, analysis, reporting, validation, and guarded execution.

## Coverage Status

| Area | Adapter capability | MCP route | Safety |
| --- | --- | --- | --- |
| Advertiser account | list, get, inspect, update plan | direct ad account tools, `advertiser`, `bc` | updates require approval |
| Campaigns | list, get, create, update, status, duplicate plan | direct Smart+ tools, `campaign` | writes paused/disabled; status separate |
| Smart+ campaigns | list, get, create, update, status, app bootstrap plan | direct upgraded Smart+ tools, `smart_plus` | writes approval-gated |
| Ad groups | list, get, create, update, budget, status | direct Smart+ tools, `adgroup` | budget/status separate approval |
| Smart+ ad groups | list, get, create, update, budget, status | direct upgraded Smart+ tools, `smart_plus` | budget/status separate approval |
| Ads | list, get, create, update, status, review | `ad`, direct Smart+ tools | create disabled; activate separate |
| Smart+ ads | list, get, create, update, status, creative status | direct upgraded Smart+ tools, `smart_plus` | writes approval-gated |
| Assets | discover, image search, video info, media references, share, delete | `file`, `creative`, direct image/video tools | Use `file_video_ad_info_get` for video info. Share/delete approval-gated. |
| Creative portfolios | list, get, select, inspect, export source, match campaign, create | direct creative portfolio tools, `creative` | create/share/delete approval-gated |
| Creative text helpers | smart text, CTA recommendation | `creative` | read-only unless saved into an ad |
| Validation | creative, ad link, promoted object | `ad`, `adgroup`, `smart_plus`, `pixel`, `app`, `catalog` | read-only |
| Targeting | regions, search, info, list, audience estimate | `audience`, `adgroup`, `ad` | read-only |
| Identities | list, Spark posts, TikTok post info, live videos, create plan | direct identity tools, `identity`, `business` | Use `tt_video_list_get` and `identity_video_info_get` when identity or Spark context is available. Create/delete approval-gated. |
| Insights | account, campaign, ad group, ad, Smart+, creative, GMV Max | direct synchronous report, `report`, `smart_plus`, `gmv_max` | read-only |
| Landing and app | URL/app extraction, W2A routing, SKU/product grouping | `report`, `ad`, `adgroup`, `smart_plus`, `app`, `catalog` | read-only |
| Reports | daily, weekly, custom, depth-aware sources | [tiktok-report-runner](tiktok-report-runner.md) | read-only unless user approves fixes |
| Rebuild | export state, destination gap analysis, staged plan, resumable log | all read groups plus write groups after approval | staged approval |

## Read-First Object Routes

For any object request:

1. Call `ensure_mcp_ready`.
2. Identify the object level: advertiser, campaign, Smart+ campaign, ad group, Smart+ ad group, ad, Smart+ ad, asset, identity, catalog, app, pixel, or creative portfolio.
3. Prefer direct MCP tools when a matching direct tool exists.
4. Otherwise run `tool_list`, then `tool_get` for the matching group, then `tool_execute`.
5. Preserve the exact requested object IDs, filters, fields, page size, cursor, and date range in `sources/*.json` when a report or audit is requested.

## Entity Detail Expectations

Entity reads should return these normalized fields when available:

- `platform`
- `advertiser_id`
- `entity_level`
- `entity_id`
- `name`
- `objective`
- `optimization_goal`
- `promotion_type`
- `operation_status`
- `secondary_status`
- `review_status`
- `budget`
- `bid_strategy`
- `campaign_automation_type`
- `identity_id`
- `app_id`
- `pixel_id`
- `catalog_id`
- `landing_url`
- `creative_asset_ids`
- `raw_source`

If a field is unavailable from the selected MCP tool, mark it as `unavailable`, not blank.

## Write Gate

Before any create, update, share, delete, budget, status, duplicate, or asset-transfer action:

1. Read the target account and existing object state.
2. Validate required assets and promoted object relationships.
3. Present the exact operation summary, target IDs, changed fields, default paused/disabled state, and expected risks.
4. Ask for explicit approval.
5. Execute only the approved operation.
6. Run post-write readback and blocking-error/review checks.
7. Ask separately before activation.

## Unsupported Handling

Return one of:

- `supported`
- `supported_empty`
- `unsupported`
- `permission_denied`
- `rate_limited`
- `partial`
- `degraded`

Never collapse API rejection, no data, no permission, and missing source into the same status.
