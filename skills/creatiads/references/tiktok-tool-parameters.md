# TikTok MCP Tool Parameter Reference

Auto-generated from live MCP schema inspection on 2026-05-23 against 443-tool inventory.

## Core Read Tools

### ad_get
- **Route**: L1 `ad.ad_get`, API `/ad/get/`
- **Required**: `advertiser_id`
- **Key filters** (`filtering` object):
  - `ad_ids`: string[], max 100
  - `ad_ids_v2`: string[], max 100 — works for both Manual Ad IDs and Upgraded Smart+ Ad IDs. When filtering by Smart+ IDs, only limited fields returned.
  - `adgroup_ids`: string[], max 100
  - `campaign_ids`: string[], max 100
  - `campaign_automation_type`: `MANUAL` | `SMART_PLUS` | `UPGRADED_SMART_PLUS`
  - `creation_filter_start_time` / `creation_filter_end_time`: `YYYY-MM-DD HH:MM:SS` UTC, ≤6 month range recommended
  - `primary_status`: string
  - `secondary_status`: string
  - `objective_type`: string
  - `optimization_goal`: string
  - `destination`: `APP` | `TIKTOK_INSTANT_PAGE` | `WEBSITE` | `SOCIAL_MEDIA_APP` | `PHONE_CALL`
  - `buying_types`: `["AUCTION","RESERVATION_RF"]` (default) | `["RESERVATION_TOP_VIEW"]` (cannot combine)
  - `creative_material_mode`: `CUSTOM` | `DYNAMIC` | `SMART_CREATIVE`
- **Pagination**: `page` (int, ≥1), `page_size` (int, 1–1000, default 10)

### adgroup_get
- **Route**: L1 `adgroup.adgroup_get`, API `/adgroup/get/`
- **Required**: `advertiser_id`
- **Key filters**:
  - `adgroup_ids`: string[], max 100
  - `campaign_ids`: string[], max 100
  - `adgroup_name`: string (non-fuzzy match)
  - `campaign_automation_type`: `MANUAL` | `SMART_PLUS` | `UPGRADED_SMART_PLUS`
  - `promotion_type`: `APP` | `WEBSITE` | `INSTANT_FORM` | `LEAD_GEN_CLICK_TO_TT_DIRECT_MESSAGE` | `LEAD_GEN_CLICK_TO_SOCIAL_MEDIA_APP_MESSAGE` | `LEAD_GEN_CLICK_TO_CALL`
  - `primary_status`: string
  - `billing_events`: string[]
  - `bid_strategy`: `BID_STRATEGY_COST_CAP` | `BID_STRATEGY_BID_CAP` | `BID_STRATEGY_MAX_CONVERSION` | `BID_STRATEGY_LOWEST_COST`
- **Pagination**: `page` (≥1), `page_size` (1–1000, default 10; max 100 for TopView)

### campaign_get
- **Route**: L1 `campaign.campaign_get`, API `/campaign/get/`
- **Required**: `advertiser_id`
- **Key filters**:
  - `campaign_ids`: string[], max 100
  - `campaign_name`: string (fuzzy match supported)
  - `campaign_automation_type`: `MANUAL` | `SMART_PLUS` | `UPGRADED_SMART_PLUS`
  - `objective_type`: string
  - `campaign_type`: `REGULAR_CAMPAIGN` | `IOS14_CAMPAIGN`
  - `sales_destination`: `TIKTOK_SHOP` | `WEBSITE` | `APP` | `WEB_AND_APP`
  - `is_smart_performance_campaign`: boolean — true = Smart+/Smart Performance Web
  - `creative_campaign_type`: `["SPC","SEARCH_CAMPAIGN","OTHER"]`
  - `buying_types`: `["AUCTION","RESERVATION_RF"]` (default) | `["RESERVATION_TOP_VIEW"]`
- **Pagination**: `page` (≥1), `page_size` (1–1000, default 10)

### report_integrated_get
- **Route**: L0 direct, API `/report/integrated/get/`
- **Required**: `advertiser_id`, `report_type`, `dimensions`, `start_date`, `end_date`
- **Key params**:
  - `report_type`: `BASIC` | `AUDIENCE` (for audience dimensions) | `PLAYABLE_MATERIAL` | `CATALOG` | `BC` | `TT_SHOP`
  - `data_level`: `AUCTION_AD` | `AUCTION_ADGROUP` | `AUCTION_CAMPAIGN` | `AUCTION_ADVERTISER`
  - `dimensions`: string[] — common: `advertiser_id`, `campaign_id`, `adgroup_id`, `ad_id`, `ad_id_v2`, `stat_time_day`, `country_code`, `age`, `gender`, `placement`, `platform`
  - `metrics`: string[] — common: `spend`, `impressions`, `clicks`, `conversion`, `result`, `ctr`, `cpc`, `cpm`, `cost_per_result`, `video_play_actions`, `total_purchase_value`, `total_active_pay_roas`
  - `start_date` / `end_date`: `YYYY-MM-DD`. Max 30 days when dimensions include `stat_time_day`; max 365 days otherwise.
  - `page_size`: 1–1000, default 10
  - **Limit**: 20,000 ads max per query; use filters for larger accounts.

### file_image_ad_info_get
- **Route**: L1 `file.file_image_ad_info_get`, API `/file/image/ad/info/`
- **Required**: `advertiser_id`, `image_ids` (string[], max 100)
- **Note**: IDs for thumbnails returned by `/ad/get/` from TikTok Ads Manager may not work — those thumbnails weren't uploaded to Asset Library.

### file_video_ad_info_get
- **Route**: L1 `file.file_video_ad_info_get`, API `/file/video/ad/info/`
- **Required**: `advertiser_id`, `video_ids` (string[], max 60)
- **Response fields**: `video_cover_url` (formerly `poster_url`), `preview_url` (formerly `url`), `preview_url_expire_time`

### tt_video_list_get
- **Route**: L1 `tt_video.tt_video_list_get`, API `/tt_video/list/`
- **Required**: `advertiser_id`
- **Optional**: `item_types` (`["VIDEO","CAROUSEL"]`), `keyword` (max 500 chars for text, min 19 chars for item_id), `page`, `page_size` (1–50, default 20)

### changelog_task_create
- **Route**: L1 `changelog.changelog_task_create`, API `/changelog/task/create/`
- **Required**: `advertiser_id`
- **Optional**: `start_time`, `end_time` (`YYYY-MM-DD HH:MM:SS`, max 30-day gap), `object_type` (`AD` | `ADGROUP` | `ADVERTISER` | `CAMPAIGN` | `INSTANT_FORM`), `object_ids`, `operation_types` (`["CREATE","AUDIT","STATUS","UPDATE","DELETE","DOWNLOAD_LEADS","SUBSCRIBE_FORM","UNSUBSCRIBE_FORM"]`), `module` (`BIDDING_AND_OPTIMIZATION` | `BUDGET` | `STATUS` | `TARGETING`), `order_fields`, `timezone`

## Batch Size Limits

| Tool | Batch Field | Max Batch Size |
|---|---|---|
| `ad_get` | `ad_ids` | 100 |
| `adgroup_get` | `adgroup_ids` | 100 |
| `campaign_get` | `campaign_ids` | 100 |
| `smart_plus_ad_get` | `smart_plus_ad_ids` | **50** |
| `smart_plus_adgroup_get` | `adgroup_ids` | 100 |
| `smart_plus_campaign_get` | `campaign_ids` | 100 |
| `file_image_ad_info_get` | `image_ids` | 100 |
| `file_video_ad_info_get` | `video_ids` | **60** |
| `tt_video_list_get` | page_size | 50 |
| `ad_status_update` | `ad_ids` | 20 |
| `adgroup_status_update` | `adgroup_ids` | 20 |
| `campaign_status_update` | `campaign_ids` | 20 |
| `Update_the_statuses_of_Upgraded_Smart_Ads` | `smart_plus_ad_ids` | 20 |
| `report_integrated_get` | page_size | 1000 |
| `catalog_product_get` | `product_ids` | 1000 |

## Cross-Tool Dependency Chains

### Creating a Campaign → Ad Group → Ad (Regular)

```
campaign_create (L1 campaign)
  ├── objective_type: APP_PROMOTION | WEB_CONVERSIONS | LEAD_GENERATION
  ├── budget_mode: BUDGET_MODE_DYNAMIC_DAILY_BUDGET | BUDGET_MODE_TOTAL | BUDGET_MODE_INFINITE | BUDGET_MODE_DAY
  ├── campaign_type: REGULAR_CAMPAIGN (default)
  └── Returns: campaign_id

adgroup_create (L1 adgroup — actually, there's no regular adgroup_create.
  Regular ad group creation needs Smart+ flow: smart_plus_adgroup_create)
  ├── campaign_id (from step 1)
  ├── promotion_type: APP_ANDROID | APP_IOS | WEBSITE | LEAD_GENERATION | ...
  ├── optimization_goal: must be valid for objective_type
  ├── billing_event: OCPM (default for conversion goals) | CPC (for CLICK goal)
  ├── bid_type: BID_TYPE_NO_BID | BID_TYPE_CUSTOM
  └── Returns: adgroup_id

ad_create (L1 ad)
  ├── adgroup_id (from step 2)
  ├── creative_list: [ { creative_info: { ad_format: SINGLE_VIDEO | CAROUSEL_ADS, ... } } ]
  └── Returns: ad_id
```

### Creating a Smart+ Campaign → Ad Group → Ad

```
smart_plus_campaign_create (L0)
  ├── objective_type: APP_PROMOTION | WEB_CONVERSIONS | LEAD_GENERATION
  ├── campaign_name
  ├── budget, budget_mode
  └── Returns: campaign_id

smart_plus_adgroup_create (L0)
  ├── campaign_id
  ├── promotion_type: APP_ANDROID | APP_IOS | WEBSITE | LEAD_GENERATION | ...
  ├── optimization_goal
  ├── bid_type, billing_event
  ├── targeting_spec.location_ids (required!)
  ├── schedule_type: SCHEDULE_FROM_NOW | SCHEDULE_START_END
  └── Returns: adgroup_id

smart_plus_ad_create (L0)
  ├── adgroup_id
  ├── creative_list: max 50 creatives
  └── Returns: ad_id (operation_status defaults to ENABLE — PAUSE manually!)
```

### Key Enum Compatibility Matrix

**objective_type → valid optimization_goals**:

| objective_type | Valid optimization_goals |
|---|---|
| `APP_PROMOTION` | `INSTALL`, `IN_APP_EVENT`, `VALUE`, `CLICK` |
| `WEB_CONVERSIONS` | `CONVERT`, `VALUE`, `CLICK`, `TRAFFIC_LANDING_PAGE_VIEW` |
| `LEAD_GENERATION` | `LEAD_GENERATION`, `CONVERT`, `VALUE`, `CONVERSATION`, `CLICK` |

**optimization_goal → billing_event**:

| optimization_goal | billing_event |
|---|---|
| `CLICK` | `CPC` |
| `INSTALL`, `IN_APP_EVENT`, `VALUE`, `CONVERT`, `LEAD_GENERATION`, `CONVERSATION`, `TRAFFIC_LANDING_PAGE_VIEW` | `OCPM` |

### ID Routing Rules

```
ad_id in report with campaign_automation_type=UPGRADED_SMART_PLUS_CREATIVE
  → This is a CREATIVE identity → use for creative tables, previews, retention

ad_id_v2 in report with campaign_automation_type=UPGRADED_SMART_PLUS
  → This is smart_plus_ad_id → use for landing URLs, config, enrichment via smart_plus_ad_get

ad_id in report without UPGRADED_SMART_PLUS flags
  → Regular ad → use ad_get (L1 dispatcher)
```

## Field Rejection Patterns

TikTok report routes can reject valid-looking aliases. Known patterns:

1. Use `conversion` not `conversions` when sync report rejects the plural
2. Audience dimensions (`age`, `gender`, `placement`, `platform`) require `report_type: AUDIENCE` after `BASIC` rejects them
3. `ad_id` and `ad_id_v2` cannot be mixed in the same report request
4. `ad_url` field may not be returned even when requested — fall back to ad detail enrichment

## Transport Notes

- The adapter uses `tool_execute` for all L1 group tools
- L0 direct tools are tried first, then dispatcher fallback
- All writes go through `stage_write()` → `approval_required` gate