# TikTok MCP Tool Map

The TikTok remote URL is `https://business-api.tiktok.com/open_mcp/tt-ads-mcp-layer`. The server exposes direct tools and a grouped dispatcher.

## Direct Tools

Prefer direct tools when available for:

- Upgraded Smart+ campaign, ad group, and ad create/get/update/status/budget.
- Ad account details.
- Synchronous reporting.
- App list, app info, and app conversion events.
- Custom conversions.
- Pixels.
- Catalogs, feeds, products, product sets, and video packages.
- Creative portfolios.
- Identity list and identity posts.
- Music list.
- Image search.
- Lead generation page IDs.

Confirmed creative-preview direct tools:

- `smart_plus_ad_get`: exact `/open_api/v1.3/smart_plus/ad/get/` equivalent for upgraded Smart+ ad detail, creative lists, media references, and landing page lists.
- `file_image_ad_info_get`: exact `/open_api/v1.3/file/image/ad/info/` equivalent for image media info.
- `file_image_ad_search`: discovery fallback when image IDs are not yet known.
- `file_video_ad_info_get`: exact `/open_api/v1.3/file/video/ad/info/` equivalent for video media info.
- `tt_video_list_get`: exact `/open_api/v1.3/tt_video/list/` equivalent for Spark Ad post list/search fallback.
- `identity_video_info_get`: exact `/open_api/v1.3/identity/video/info/` equivalent for single identity post/video info.
- `smart_plus_material_report_overview_run`: exact `/open_api/v1.3/smart_plus/material_report/overview/` equivalent for upgraded Smart+ material overview diagnostics.
- `smart_plus_material_report_breakdown_run`: exact `/open_api/v1.3/smart_plus/material_report/breakdown/` equivalent for upgraded Smart+ material breakdown diagnostics.
- `identity_get`: identity context discovery before calling identity post routes.

## Dispatcher Tools

Use the dispatcher when a direct tool is not enough:

- `tool_list`: discover L1 groups and summaries.
- `tool_get`: fetch schema and full descriptions for target tools.
- `tool_execute`: execute a grouped tool with a request payload.

Confirmed creative-preview dispatcher tools:

- `ad_get`: exact `/open_api/v1.3/ad/get/` equivalent for regular ad detail.
- `/open_api/v1.3/ad/aco/get/`: no v2 `new_name` in the official mapping; mark Smart Creative material references `structured_unavailable` when only ACO material detail is needed.

The preview-critical video, Spark post, identity post, and upgraded Smart+ material-report routes have direct MCP mappings. If one of these tools is not present at runtime, mark the individual source `structured_unavailable` and continue with the remaining MCP evidence; do not use a non-MCP data source.

## Important Groups

- `ad`: regular ad create, get, update, status, review, Smart Creative material, audience estimate.
- `adgroup`: regular ad group get, update, budget, status, review, appeal, R&F helpers.
- `campaign`: regular campaign create, get, update, status, copy task, quota.
- `smart_plus`: Smart+ review, preview, creative status, creative reports, appeal.
- `advertiser`: balance, budget, transactions, account update.
- `audience`: custom audiences, saved audiences, interest, behavior, hashtag, geo, device, carrier, brand safety, Pangle, audience insights.
- `bc`: Business Center accounts, assets, members, billing, invoices, partner, payment, account creation, asset assignment.
- `business`: organic business account content, posts, comments, messaging, Spark Ads, webhooks, URL properties.
- `catalog`: catalog, feed, product, product set, video, trends, event source binding.
- `creative`: portfolios, smart text, CTA recommendations, preview, reports, asset share and delete.
- `file`: image, video, music upload, search, info, thumbnails, chunk upload.
- `gmv_max`: GMV Max campaign, shop, product, identity, report, authorization, session.
- `identity`: identity create/delete/info, posts, live videos, music authorization.
- `pixel`: pixel create/update, pixel events, event stats, web event reporting.
- `report`: async reports, creative reports, in-second performance, benchmarks.
- `tto`: TikTok One creator marketplace, creator discovery, insights, campaign, anchor, video linking.

## Workflow Mapping

- `list_accounts`: ad account direct tools plus Business Center asset discovery when needed.
- `discover_assets`: Business Center assets, identity, app, pixel, custom conversion, catalog, product, lead page, creative portfolio, image, video, music, and file discovery.
- `get_entities`: campaign, adgroup, ad, Smart+ direct tools and grouped tools.
- `get_pages`: lead generation page direct tool and business/page group tools where applicable.
- `get_catalogs`: direct catalog tools and `catalog` group.
- `create_campaign`: Smart+ direct tools or `campaign.campaign_create`.
- `create_adset_or_adgroup`: Smart+ direct tools or `adgroup` group for eligible flows.
- `create_ad`: Smart+ direct tools or `ad.ad_create`.
- `update_entity`: Smart+ direct tools or campaign/adgroup/ad update tools.
- `activate_entity`: Smart+ direct status tools or campaign/adgroup/ad status tools.
- `validate_creative`: `ad`, `creative`, `file`, `identity`, app, pixel, and landing evidence checks.
- `validate_ad_link`: ad group/ad detail plus promoted object, app, pixel, catalog, identity, and landing evidence checks.
- `validate_promoted_object`: ad group, Smart+, app, pixel, catalog, identity, and objective compatibility checks.
- `get_blocking_errors`: review info and diagnostic tools.
- `get_insights`: direct synchronous report, `report` group, Smart+ report tools, GMV Max report tools.
- `run_gmv_max_report`: use [gmv-max-reporting](gmv-max-reporting.md). Pull GMV Max stores, Product/Live GMV Max campaign discovery, GMV Max account/campaign/product/creative/duration reports, campaign item previews, store products, and optional custom-anchor/video-pool preview fallbacks. Do not use regular auction campaign/adgroup/ad emptiness as a failure signal for GMV Max-first accounts.
- `run_report`: [tiktok-report-runner](tiktok-report-runner.md) source plan using sync report, audience reports, Smart+ reports, creative reports, changelog/activity tools, and enrichment reads.
- `get_activity_changelog`: `report`, advertiser change-log/task tools when exposed, or dispatcher-discovered changelog equivalents.
- `probe_metrics`: grouped report calls that classify metrics as active, supported-empty, unsupported, invalid-combination, permission-denied, or rate-limited.
- `recommend_metric_preset`: advertiser type plus metric probe evidence mapped to core, vertical, and measurement-risk metrics.
- `get_dataset_or_pixel_health`: pixel, app, custom conversion, catalog diagnostics.
- `analyze_landing_or_app_path`: report rows plus ad, adgroup, Smart+ ad, app, catalog, and identity detail.
- `analyze_audience_breakdowns`: `AUDIENCE` report routes for country, age/gender, placement, and device with fallbacks.
- `analyze_creative_retention`: ad-level or Smart+ creative-level reports plus video metrics and targeted preview enrichment.
- `get_creative_previews`: use [tiktok-creative-preview-resolution](tiktok-creative-preview-resolution.md). Resolve final report rows through `ad_get`, `smart_plus_ad_get`, `file_image_ad_info_get`, `file_video_ad_info_get`, `tt_video_list_get`, `identity_video_info_get`, `identity_get`, and upgraded Smart+ material report tools where schemas support the required filters. Do not count non-URL references as preview coverage.
- `analyze_measurement_attribution`: metric probe plus attribution, SKAN, SAN, app/web/W2A, result, and value source checks.
- `plan_budget_bid_actions`: report and entity reads that classify scale, maintain, fix, reduce, or pause recommendations without executing writes.
- `classify_advertiser_type`: top-spend report, objectives, promotion type, landing evidence, app evidence, catalog/shop evidence.
- `generate_report_sources`: report rows, top object details, review info, creative assets, landing/app evidence, catalog/pixel/app health.
- `plan_cross_account_rebuild`: source export, destination gap analysis, staged payload plan, validation, and resumable record.

## Landing And App Evidence

For URL and app-path analysis:

- Pull report rows by ad or Smart+ ad identity first.
- Enrich top spend objects with ad, ad group, Smart+ ad, app, catalog, and identity details.
- Extract landing URLs, app IDs, app names, store URLs, product URLs, catalog IDs, and shop evidence from the enriched object set.
- Mark unresolved spend as `partial` with object IDs and the missing source.

## Cold Start Routes

For a product page or app page:

- Use strategy extraction from the user-provided page or brief for offer, audience, creative, and test design.
- Use app, pixel, custom conversion, catalog, identity, page, audience, and creative groups only when an advertiser or asset ID is available.
- Use audience estimate, targeting, creative, file, catalog, app, and pixel tools to validate a proposed launch structure.
- Use create tools only after approval, and keep all created objects disabled or paused.

## Rebuild Routes

For cross-account rebuilds:

- Source read: campaign, adgroup, ad, Smart+ direct tools, catalog, creative, file, identity, app, pixel, and page tools.
- Destination read: advertiser, Business Center, assets, identity, app, pixel, catalog, and permissions.
- Gap analysis: compare source dependencies with destination availability.
- Plan writes: campaign, adgroup, ad, Smart+ creation, asset share, file upload, identity creation, catalog or product setup where supported.
- Execute writes only after explicit approval, with activation as the final separate step.

## Parity References

- Use [tiktok-operation-map](tiktok-operation-map.md) for explicit operation coverage.
- Use [tiktok-cli-sdk-mcp-parity](tiktok-cli-sdk-mcp-parity.md) when translating previous TikTok command behavior or checking API route parity.
- Use [tiktok-analysis-playbooks](tiktok-analysis-playbooks.md) for metric probes, advertiser classification, landing/app, audience, creative retention, budget/bid, and measurement.
- Use [tiktok-report-runner](tiktok-report-runner.md) for daily, weekly, custom, activity, preview, and HTML report behavior.
- Use [gmv-max-reporting](gmv-max-reporting.md) for Product GMV Max / TikTok Shop report mode, product/item-group enrichment, item previews, and GMV Max HTML/audit rules.
- Use [tiktok-validation-and-rebuild](tiktok-validation-and-rebuild.md) for prelaunch validation, bottleneck diagnosis, and cross-account rebuild.
