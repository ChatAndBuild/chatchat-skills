# Parameter quick reference — creative-fatigue-rotation-planner (verified on the live MCP)

## Ad-level report — `report_integrated_get` (recent, sync) / `report_task_*` (baseline, async)
| Param | Value |
|---|---|
| `advertiser_id` | from Stage 0 |
| `report_type` | `BASIC` |
| `data_level` | `AUCTION_AD` |
| `dimensions` | `["ad_id"]` |
| `metrics` | `spend, impressions, clicks, ctr, conversion, conversion_rate, ad_name` (+ `campaign_name`) |
| `start_date` / `end_date` | recent = last 3 days; baseline = last 30 days; `YYYY-MM-DD`, `end_date ≤ today` |
| `filtering` | optional, e.g. `[{"field_name":"campaign_ids","filter_type":"IN","filter_value":"[\"<id>\"]"}]` |
| `order_field` / `order_type` | `spend` / `DESC` |
| `page_size` | ≤ 1000; paginate via `page_info` |

Response: `data.list[].{dimensions:{ad_id}, metrics:{…strings…}}`, plus `data.page_info`.

> Metric name is **`conversion`** (singular); rate is **`conversion_rate`**. `conversions` → `40002`.
> Values are strings; VND has no decimals.

## Sync vs. async
- **Recent (3 days, ad level, small)** → **sync** `report_integrated_get` (L0).
- **Baseline (30 days, ad level)** → **async** `report_task_create` → `report_task_check` (poll) →
  `report_task_download` (`tool_execute`). `FAILED` → `E104_ASYNC_FAILED`.

## Ad ↔ creative mapping
`smart_plus_ad_get` (L0) / `ad_get` (`tool_execute`): `ad_id` → ad name, creative/material id, status.

## Optional library scan (off the critical path, non-blocking)
`file_video_ad_search` / `file_image_ad_search` (`tool_execute`). If error/empty → "No unused library
assets found," continue. There is also an allowlist-only `creative_fatigue_get` — optional enhancement.

## Account / resolve
`advertiser_info_get` (currency/timezone). `auth_advertiser_get` / `bc_get` may be empty → ask the user
to paste an `advertiser_id`/`bc_id`. `40001` → not authorized on that id (E102).

## Derived metrics
`CVR = conversion / clicks` · `CPA = spend / conversion`.

## Hard rules
- **Never** call `ad_update` / `smart_plus_ad_update` / `*_status_update` / `*_material_status_update`
  / `file_*_upload` / `adgroup_appeal` / `*_delete` / `*_create` (except `report_task_create`). Read-only.
- **Never** fabricate an `n/a` metric.
