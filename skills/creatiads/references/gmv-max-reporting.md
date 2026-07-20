# TikTok GMV Max Reporting

Use this reference for TikTok Shop Product GMV Max reports, creative/item analysis, store/product
enrichment, and HTML reporting.

GMV Max is a separate report mode, not a regular auction campaign report with extra sources. A
GMV Max-first account may have no meaningful regular `AUCTION_CAMPAIGN`, `AUCTION_ADGROUP`, `AUCTION_AD`,
activity, or changelog rows. Do not mark the report degraded only because those regular auction sources
are empty when GMV Max sources are present.

## Scope

Supported by this skill:

- read TikTok Shop stores and GMV Max availability
- discover Product GMV Max and Live GMV Max campaigns
- pull account, campaign, product/item-group, creative/item, and duration GMV Max reports
- enrich item groups with store product details
- enrich creative/items with campaign item previews, identity video info, custom anchor videos, and GMV Max video pool diagnostics
- generate or guide GMV Max HTML reports with cached product, preview, and avatar images
- audit coverage, reconciliation, preview coverage, and data-quality notes

Not supported without a separate explicit approval-gated ops flow:

- closing or excluding creative items
- changing campaign status, budget, target ROI, sessions, or product selection
- creating or deleting GMV Max campaigns

## MCP Tool Map

Prefer direct tools if exposed in the runtime. Otherwise use `tool_execute` with the exact L1 tool name
after verifying the schema with `tool_get`.

| Source | Tool | Notes |
|---|---|---|
| Store list | `gmv_max_store_list_get` or `store_list_get` | Filter `is_gmv_max_available=true`; capture `store_id`, `store_authorized_bc_id`, `store_name`. |
| Campaign discovery | `gmv_max_campaign_get` | Discovery uses `PRODUCT_GMV_MAX` / `LIVE_GMV_MAX`. May filter by `store_ids`. |
| Campaign info / item previews | `campaign_gmv_max_info_get` | Preferred preview source for `item_list[]`, `video_info`, `preview_url`, and `identity_info`. |
| GMV Max reports | `gmv_max_report_get` | Report filtering uses `PRODUCT` / `LIVE`, not discovery enum values. |
| Store products | `store_product_get` | Fetch by `bc_id`, `store_id`, and `filtering.item_group_ids` in batches of at most 10. |
| Identity video info | `identity_video_info_get` | Batch by `(identity_type, identity_id, identity_authorized_bc_id)`; at most 20 `item_ids`. |
| Custom anchor videos | `gmv_max_custom_anchor_video_list_get` | Optional preview fallback; zero hits are normal. |
| GMV Max video pool | `gmv_max_video_get` | Diagnostic/source-pool only. Use rows only when they join back to report `item_id`. |
| Bid recommendation | `gmv_max_bid_recommend_get` | Read-only planning signal; do not apply budget/ROI changes without approval. |

## Source Plan

For a standard Product GMV Max weekly report, materialize:

- `gmv_max_stores.json`
- `gmv_max_campaigns_product.json`
- `gmv_max_campaigns_live.json` when Live GMV Max is in scope; otherwise `not_applicable`
- `current_gmv_max_account.json` and `previous_gmv_max_account.json`
- `current_gmv_max_campaign.json` and `previous_gmv_max_campaign.json`
- `current_gmv_max_campaign_day.json` and `previous_gmv_max_campaign_day.json`
- `current_gmv_max_product.json` and `previous_gmv_max_product.json`
- `current_gmv_max_creative.json` and `previous_gmv_max_creative.json`
- `current_gmv_max_duration.json` and `previous_gmv_max_duration.json`
- `gmv_max_campaign_item_previews.json`
- `gmv_max_store_products.json`
- optional `gmv_max_custom_anchor_videos.json`, `gmv_max_videos.json`, `gmv_max_resolved_item_previews.json`

Debug probes such as product-day or creative-day compatibility checks may be written, but they are not
required standard report sources.

## Report Levels

Request metrics only at supported GMV Max levels.

Account:

- dimensions: `["advertiser_id"]`
- metrics: `cost`, `orders`, `cost_per_order`, `gross_revenue`, `roi`, `net_cost`

Campaign:

- dimensions: `["campaign_id"]`
- daily dimensions: `["campaign_id", "stat_time_day"]`
- metrics: `roas_bid`, `cost`, `net_cost`, `orders`, `cost_per_order`, `gross_revenue`, `roi`

Product / Item Group:

- dimensions: `["item_group_id"]`
- metrics: `product_status`, `orders`, `gross_revenue`
- do not request creative playback or product click metrics at this level in the standard report

Creative / Item:

- standard dimensions: `["campaign_id", "item_group_id", "item_id"]`
- daily dimensions: `["campaign_id", "item_group_id", "item_id", "stat_time_day"]` or `["item_id", "stat_time_day"]`
- metrics: `creative_delivery_status`, `cost`, `orders`, `cost_per_order`, `gross_revenue`, `roi`,
  `product_impressions`, `product_clicks`, `product_click_rate`, `ad_click_rate`,
  `ad_conversion_rate`, `ad_video_view_rate_2s`, `ad_video_view_rate_6s`,
  `ad_video_view_rate_p25`, `ad_video_view_rate_p50`, `ad_video_view_rate_p75`,
  `ad_video_view_rate_p100`

Duration:

- dimensions: `["duration"]`
- metrics: `cost`, `orders`, `cost_per_order`, `gross_revenue`, `roi`, `roas_bid`

## Product / Item Group Rules

Product cards combine multiple sources:

- identity fields from `store_product_get`: image, title, item group ID, min/max price, currency
- status from Product report `product_status`
- performance from Creative rows aggregated by `item_group_id` when Creative totals reconcile

If Creative rows are missing, sampled, fast-mode, or do not reconcile with account/product totals, show only
official Product report fields and store-product identity fields. Do not invent cost, ROI, GPM, clicks, or
click rate.

Product table columns should be:

1. Product / Item Group
2. Status
3. Campaign count
4. Cost
5. Orders
6. Gross revenue
7. ROI
8. Cost per order
9. Product GPM
10. Product impressions
11. Product clicks
12. Product click rate

Do not show `gmv_max_ads_status` on Product cards.

## Creative / Item Rules

Use `current_gmv_max_creative.json` as the main creative source. Aggregate concrete video items by
`item_id` across campaigns and item groups.

- `item_id=-1` means Product Card / All Products. Exclude it from concrete creative rankings and show it as a separate Product Card aggregate.
- Default to the top 40 rendered creative rows, not only the top 15.
- Attempt preview and image caching for every rendered row.
- `creative_types` and `creative_delivery_statuses` must not be used together in the same report request.
- When there are multiple campaigns or item groups, avoid requesting attribute metrics that the report level cannot support.

Creative table columns should include:

- Preview
- Creative / account / post
- Delivery status
- Creative judgement
- Campaign count
- Cost, orders, gross revenue, ROI, ROI change
- CPM proxy, Product GPM, cost per order
- Product impressions, clicks, click rate
- 2s play rate, 6s play rate, completion rate

## Preview Resolution

Resolve previews in this order:

1. `campaign_gmv_max_info_get`: map `item_list[]` to `item_id`, cover, preview URL, identity info.
2. `identity_video_info_get`: refresh cover/video URL/copy/avatar/user name for CUSTOM_SELECTION rows with identity context.
3. Same-item cross-campaign fallback: reuse item preview from another CUSTOM_SELECTION campaign when AUTO_SELECTION lacks `item_list`.
4. `gmv_max_custom_anchor_video_list_get`: optional customized-post fallback.
5. `gmv_max_video_get`: source-pool diagnostics; use only rows that join to report `item_id`.
6. Local public item resolver only for final rendered rows missing cover or avatar, and only when non-MCP public-page fallback is explicitly acceptable for the report.

Signed TikTok media URLs may expire. Cache images whenever possible:

- `assets/gmv_max_previews/`
- `assets/gmv_max_avatars/`
- `assets/gmv_max_products/`
- `assets/tiktok_item_resolver/<item_id>/`

## Creative Judgement

Do not recommend bluntly deleting high-spend low-ROI creative. GMV Max judgement should consider life cycle,
system learning, Product GPM, interaction quality, delivery status, and account-level ROI.

Protect/observe:

- new items with only 1-2 days of data and healthy click/play signals
- items with healthy Product GPM but temporarily high CPM or early exploration cost
- low-ROI items with strong clicks, play, or product interest when account ROI is acceptable
- statuses such as `IN_QUEUE` or `LEARNING` with insufficient data

Replacement candidates:

- previously strong high-spend items that now have sharply lower ROI
- high-spend, low-ROI items without Product GPM, click-rate, or play-rate protection
- `REJECTED`, `UNAVAILABLE`, `EXCLUDED`, or similar statuses with no valid delivery or clear rejection reason

Recommended action style:

1. Prepare 5-10 new items around the core selling point with different first-three-second hooks.
2. Run old and new items together for 1-3 days.
3. Gradually release or reduce high-spend low-ROI items on day 4-5.
4. If traffic drops sharply after removal, restore old items and continue creative iteration.

## HTML And Audit Requirements

GMV Max HTML should include:

- scope / coverage header stating `report_mode=gmv_max`
- KPI cards
- executive summary
- recommended actions
- campaign drivers
- Product / Item Group table
- Creative / Item Buckets table
- creative handoff or replacement strategy
- Product Card / All Products aggregate
- data quality and provenance

Wide product and creative tables must use horizontal scrolling, stable min-widths, and non-wrapping numeric
columns. Creative copy should truncate by default and reveal full text on hover/focus.

Audit checks should confirm:

- no tokens, auth headers, callback secrets, or MCP session metadata appear in artifacts
- discovery enum values are not mixed with report enum values
- required GMV Max report levels are present
- Creative source uses the official `campaign_id + item_group_id + item_id` dimension combination
- Product performance is derived from Creative only when reconciliation is acceptable
- `item_id=-1` is excluded from concrete creative rankings
- final rendered top 40 rows have preview enrichment attempted
- remote TikTok image URLs are cached locally when possible
- missing auction campaign/adgroup/ad/activity sources do not degrade a GMV Max-first report
