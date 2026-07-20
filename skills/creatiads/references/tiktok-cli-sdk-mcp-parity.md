# TikTok Interface Parity

Use this reference when replacing previous TikTok command behavior with TikTok Ads MCP calls.

## Validation Inputs

This parity map was built from:

- 122 previous TikTok command entries.
- The underlying TikTok Business API client routes used by those commands.
- The TikTok Ads MCP tool inventory with 443 L1 API tools.

Scope:

- Replace platform reads, reports, validation, asset discovery, and approval-gated writes with MCP tools.
- Authorization is handled by [mcp-initialization](mcp-initialization.md), not by token-fetching commands.
- Generative creative production routes are not part of the core parity target.
- Do not use a non-MCP data source to fill a gap. If a confirmed route is absent at runtime, return `structured_unavailable`.

## Strict Replacement Rules

1. Start every TikTok task with `ensure_mcp_ready`.
2. Match by API route first, then by tool name, then by MCP group.
3. Prefer direct tools when the exact route is exposed.
4. Use `tool_list`, `tool_get`, and `tool_execute` only when a direct tool is absent or the schema must be verified.
5. Preserve the old command's object IDs, date windows, filters, pagination, fields, and write intent in the MCP payload.
6. For writes, read first, show the intended payload and risk, then wait for explicit approval.
7. Keep create operations paused or disabled by default; activation is a separate approval.
8. Distinguish `supported_empty`, `unsupported`, `permission_denied`, `rate_limited`, `partial`, `degraded`, and `structured_unavailable`.

## Command Family Coverage

| Previous command family | Underlying API route family | MCP replacement | Status |
| --- | --- | --- | --- |
| `tiktok campaigns *` | `/campaign/*` | `campaign_create`, `campaign_get`, `campaign_update`, `campaign_status_update`, campaign copy task tools | exact for regular campaigns |
| `tiktok smartplus-campaigns *` | `/smart_plus/campaign/*` | Direct upgraded Smart+ campaign tools when exposed by the runtime namespace | runtime exact; validate with `tool_get` |
| `tiktok adgroups *` | `/adgroup/*` | `adgroup_get`, `adgroup_update`, `adgroup_budget_update`, `adgroup_status_update`, R&F helpers | exact for regular ad groups |
| `tiktok smartplus-adgroups *` | `/smart_plus/adgroup/*` | Direct upgraded Smart+ ad group tools when exposed by the runtime namespace | runtime exact; validate with `tool_get` |
| `tiktok ads *` | `/ad/*` | `ad_create`, `ad_get`, `ad_update`, `ad_status_update`, `ad_review_info_get` | exact for regular ads |
| `tiktok smartplus-ads *` | `/smart_plus/ad/*` | `smart_plus_ad_get`, `smart_plus_ad_preview`, review, appeal, material status tools | exact for discovered Smart+ ad reads and diagnostics |
| `tiktok activities get` | `/changelog/task/*` | `changelog_task_create`, `changelog_task_check`, `changelog_task_download` | exact |
| `tiktok insights get` | `/report/integrated/get/` | Direct synchronous report tool when exposed; otherwise async report task tools with matching dimensions and metrics | runtime exact or async-compatible |
| `tiktok gmv-max-*` and GMV Max report mode | `/gmv_max/*`, `/campaign/gmv_max/*`, `/report/gmv_max/get/`, `/store/product/get/` | `gmv_max_store_list_get`, `gmv_max_campaign_get`, `campaign_gmv_max_info_get`, `gmv_max_report_get`, `store_product_get`, `identity_video_info_get`, `gmv_max_custom_anchor_video_list_get`, `gmv_max_video_get` | exact via direct or L1 dispatcher; see `gmv-max-reporting.md` |
| `tiktok insights smartplus-overview` | `/smart_plus/material_report/overview/` | `smart_plus_material_report_overview_run` | exact |
| `tiktok insights smartplus-breakdown` | `/smart_plus/material_report/breakdown/` | `smart_plus_material_report_breakdown_run` | exact |
| `tiktok landing-pages analyze` | report rows plus ad/ad group/Smart+ detail | report tool, `ad_get`, `adgroup_get`, `smart_plus_ad_get`, app, catalog, identity, and Spark post tools | exact or partial per source |
| `tiktok apps analyze` | account, app, report, campaign/ad group/ad detail | app direct tools when exposed, report tool, `campaign_get`, `adgroup_get`, `ad_get` | runtime exact for app list/info; validate schema |
| `tiktok user-type analyze` | advertiser info, report, campaign/ad group/ad detail, app/catalog/shop evidence | account direct tools, report tool, `campaign_get`, `adgroup_get`, `ad_get`, catalog, GMV Max shop/store tools | exact or partial per evidence |
| `tiktok metrics probe` | `/report/integrated/get/` | direct synchronous report tool or async report task tools | runtime exact or async-compatible |
| `tiktok audience breakdown` | report dimensions | report tool with country, age/gender, placement, device, and other supported dimensions | exact when dimensions are accepted |
| `tiktok creative-retention report` | ad-level report, ad detail, Smart+ detail, media info, Spark/identity posts | report tool, `ad_get`, `smart_plus_ad_get`, `file_image_ad_info_get`, `file_video_ad_info_get`, `tt_video_list_get`, `identity_video_info_get`, Smart+ material report tools | exact for required enrichment routes |
| `tiktok assets discover` | advertiser, BC, app, pixel, offline, catalog, store, identity | account direct tools, `bc_get`, `bc_asset_get`, app, pixel, offline, catalog, GMV Max store, identity tools | exact or runtime direct per asset |
| `tiktok assets image-info` | `/file/image/ad/info/` | `file_image_ad_info_get` | exact |
| `tiktok assets video-info` | `/file/video/ad/info/` | `file_video_ad_info_get` | exact |
| `tiktok assets video-search` | `/file/video/ad/search/` | `file_video_ad_search` | exact |
| `tiktok assets delete/share` | `/creative/asset/delete/`, `/creative/asset/share/` | `creative_asset_delete`, `creative_asset_share_get` | exact; approval-gated |
| `tiktok identities list` | `/identity/get/` | `identity_get` when exposed; identity group discovery otherwise | runtime exact; validate with `tool_get` |
| `tiktok identities create` | `/identity/create/` | no v2 `new_name` | unavailable in v2; approval-gated if restored |
| `tiktok identities video-info` | `/identity/video/info/` | `identity_video_info_get` | exact |
| `tiktok targeting regions` | `/search/region/` | `search_region_get` | exact |
| `tiktok targeting search/info/list` | `/tool/targeting/search/`, `/tool/targeting/info/`, `/tool/targeting/list/` | `tool_targeting_search`, `tool_targeting_info_get`, `tool_targeting_list_get` or dispatcher targeting tools | exact by route where exposed |
| `tiktok validate ad-link` | ad group/ad detail and promoted object dependencies | `adgroup_get`, `ad_get`, `smart_plus_ad_get`, app, pixel, catalog, identity, and URL/property tools where exposed | exact or partial per dependency |
| `tiktok validate promoted-object` | app, pixel, catalog, identity, store, VBO, URL validation | app, pixel, catalog, identity, GMV Max/store, and tool group routes | exact or partial per dependency |
| `tiktok creative-assets portfolio *` | `/creative/portfolio/*` | `creative_portfolio_create`, `creative_portfolio_get`, portfolio runtime list/select helpers when exposed | exact for create/get; runtime discovery for list/select |
| `tiktok creative-assets share-link` | `/creative/shareable_link/create/` | runtime creative share-link tool when exposed | runtime exact; approval-gated if sharing assets |
| `tiktok creative-assets smart-text` | `/creative/smart_text/generate/` | `creative_smart_text_get` | exact |

## Endpoint Replacement Table

| API route | MCP tool |
| --- | --- |
| `/ad/aco/create/` | no v2 `new_name` |
| `/ad/aco/get/` | no v2 `new_name` |
| `/ad/aco/material_status/update/` | no v2 `new_name` |
| `/ad/aco/update/` | no v2 `new_name` |
| `/ad/audience_size/estimate/` | `ad_audience_size_estimate` |
| `/ad/create/` | `ad_create` |
| `/ad/get/` | `ad_get` |
| `/ad/review_info/` | `ad_review_info_get` |
| `/ad/status/update/` | `ad_status_update` |
| `/ad/update/` | `ad_update` |
| `/adgroup/get/` | `adgroup_get` |
| `/adgroup/budget/update/` | `adgroup_budget_update` |
| `/adgroup/review_info/` | `adgroup_review_info_get` |
| `/adgroup/status/update/` | `adgroup_status_update` |
| `/adgroup/update/` | `adgroup_update` |
| `/campaign/create/` | `campaign_create` |
| `/campaign/get/` | `campaign_get` |
| `/campaign/status/update/` | `campaign_status_update` |
| `/campaign/update/` | `campaign_update` |
| `/campaign/copy/task/create/` | `campaign_copy_task_create` |
| `/campaign/copy/task/check/` | `campaign_copy_task_check` |
| `/changelog/task/create/` | `changelog_task_create` |
| `/changelog/task/check/` | `changelog_task_check` |
| `/changelog/task/download/` | `changelog_task_download` |
| `/file/image/ad/info/` | `file_image_ad_info_get` |
| `/file/image/ad/upload/` | no v2 `new_name` |
| `/file/video/ad/info/` | `file_video_ad_info_get` |
| `/file/video/ad/search/` | `file_video_ad_search` |
| `/file/video/ad/update/` | `file_video_ad_update` |
| `/file/video/ad/upload/` | no v2 `new_name` |
| `/tt_video/list/` | `tt_video_list_get` |
| `/tt_video/info/` | `tt_video_info_get` |
| `/identity/create/` | no v2 `new_name` |
| `/identity/video/info/` | `identity_video_info_get` |
| `/identity/info/` | `identity_info_get` |
| `/identity/live/get/` | `identity_live_get` |
| `/smart_plus/ad/appeal/` | `smart_plus_ad_appeal` |
| `/smart_plus/ad/material_status/update/` | `smart_plus_ad_material_status_update` |
| `/smart_plus/ad/preview/` | `smart_plus_ad_preview` |
| `/smart_plus/ad/review_info/` | `smart_plus_ad_review_info_get` |
| `/smart_plus/material/review_info/` | `smart_plus_material_review_info_get` |
| `/smart_plus/material_report/overview/` | `smart_plus_material_report_overview_run` |
| `/smart_plus/material_report/breakdown/` | `smart_plus_material_report_breakdown_run` |
| `/creative/asset/delete/` | `creative_asset_delete` |
| `/creative/asset/share/` | `creative_asset_share_get` |
| `/creative/portfolio/create/` | `creative_portfolio_create` |
| `/creative/portfolio/get/` | `creative_portfolio_get` |
| `/creative/smart_text/generate/` | `creative_smart_text_get` |
| `/creative/cta/recommend/` | `creative_cta_recommend_get` |
| `/creative/ads_preview/create/` | `creative_ads_preview_create` |
| `/creative/report/get/` | `creative_report_get` |
| `/creative_fatigue/get/` | `creative_fatigue_get` |
| `/bc/get/` | `bc_get` |
| `/bc/asset/get/` | `bc_asset_get` |
| `/bc/asset/assign/` | `bc_asset_assign` |
| `/bc/asset/unassign/` | `bc_asset_unassign` |
| `/advertiser/balance/get/` | `advertiser_balance_get` |
| `/advertiser/transaction/get/` | `advertiser_transaction_get` |
| `/advertiser/update/` | `advertiser_update` |
| `/catalog/get/` | `catalog_get` when exposed; otherwise catalog group discovery |
| `/catalog/eventsource_bind/get/` | `catalog_eventsource_bind_get` |
| `/catalog/video/get/` | `catalog_video_get` |
| `/catalog/set/product/get/` | `catalog_set_product_get` |
| `/offline/get/` | `offline_get` |
| `/custom_conversion/get/` | `custom_conversion_get` |
| `/store/list/` | `store_list_get` |
| `/gmv_max/store/list/` | `gmv_max_store_list_get` |
| `/gmv_max/campaign/get/` | `gmv_max_campaign_get` |
| `/campaign/gmv_max/info/` | `campaign_gmv_max_info_get` |
| `/campaign/gmv_max/session/get/` | `campaign_gmv_max_session_get` |
| `/campaign/gmv_max/session/list/` | `campaign_gmv_max_session_list_get` |
| `/report/gmv_max/get/` | `gmv_max_report_get` |
| `/gmv_max/video/get/` | `gmv_max_video_get` |
| `/gmv_max/custom_anchor_video_list/get/` | `gmv_max_custom_anchor_video_list_get` |
| `/gmv_max/bid/recommend/` | `gmv_max_bid_recommend_get` |
| `/gmv_max/identity/get/` | `gmv_max_identity_get` |
| `/gmv_max/exclusive_authorization/get/` | `gmv_max_exclusive_authorization_get` |
| `/store/product/get/` | `store_product_get` |
| `/search/region/` | `search_region_get` |
| `/tool/targeting/search/` | `tool_targeting_search` |
| `/tool/targeting/info/` | `tool_targeting_info_get` |
| `/tool/targeting/list/` | `tool_targeting_list_get` |
| `/tool/bid/recommend/` | `tool_bid_recommend` |
| `/tool/diagnosis/get/` | `tool_diagnosis_get` |
| `/report/task/create/` | `report_task_create` |
| `/report/task/check/` | `report_task_check` |
| `/report/task/download/` | no v2 `new_name` |
| `/report/task/cancel/` | `report_task_cancel` |
| `/report/ad_benchmark/get/` | `report_ad_benchmark_get` |
| `/report/video_performance/get/` | `report_video_performance_get` |

## Runtime-Validated Routes

Some routes used by the previous command set may be exposed as direct tools outside the 443 L1 inventory or may require dispatcher discovery:

- account list/details and advertiser info
- app list/info
- pixel list
- identity list
- synchronous integrated reports
- URL validation and VBO status checks
- creative portfolio list/select/export helpers
- upgraded Smart+ campaign and ad group CRUD routes

For these routes:

1. Run `tool_list`.
2. Use `tool_get` to confirm the exact schema and route.
3. Execute only if the route, required filters, and requested fields are supported.
4. Otherwise return `structured_unavailable` with the missing route and continue with other evidence.

## Report Source Implications

Formal TikTok reports should now query these source families when the depth requires them:

- `current_*` and `previous_*` reports through synchronous or async report MCP tools.
- `smart_plus_ads.json` through upgraded Smart+ ad tools.
- `creative_previews.json` through ad detail, Smart+ ad detail, Smart Creative material, image info, video info, Spark post, identity post, and Smart+ material report tools.
- `landing_app_paths.json` through report destination fields plus ad/ad group/Smart+ detail, app, catalog, identity, and store evidence.
- `audience_breakdowns.json` through supported report dimensions and audience tools.
- `activities.json` through changelog task create/check/download tools.

Every generated report must include route-level source status in `manifest.json` and `validation_summary.json`.
