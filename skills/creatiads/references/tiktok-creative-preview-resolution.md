# TikTok Creative Preview Resolution

Use this reference whenever a TikTok report, creative review, fatigue analysis, or ad table needs creative preview evidence.

## Principle

Do not mark a row as `with_preview` unless the MCP result contains a concrete preview artifact:

- `preview_image_url`
- `thumbnail_url`
- `cover_url`
- `image_url`
- `video_url`
- `playable_url`
- `preview_url`
- `permalink_url`
- `spark_post_url`

An asset ID, Spark post ID, creative ID, or media ID is useful evidence, but it is not a preview by itself. Store it as `asset_reference`, `spark_post_reference`, or `creative_reference`, and do not count it in `preview_coverage.with_preview`.

## Output Schema

Each row in `sources/creative_previews.json` should use this shape:

```json
{
  "ad_id": "string",
  "ad_id_v2": "string|null",
  "smart_plus_ad_id": "string|null",
  "ad_name": "string",
  "preview_status": "inline_image | action_url_only | spark_post_url | asset_reference | spark_post_reference | permission_denied | unsupported | structured_unavailable | supported_empty | unavailable",
  "preview_image_url": "string|null",
  "preview_action_url": "string|null",
  "preview_url_kind": "thumbnail | cover | image | video | playable | preview | spark_post | none",
  "source_tool": "string",
  "source_fields": [],
  "reference_ids": {},
  "reason": "string|null"
}
```

`preview_status` values that count as preview coverage:

- `inline_image`
- `action_url_only`
- `spark_post_url`

Everything else is retained for diagnosis but does not count as a fetched preview.

## Resolution Order

Start from final report rows only. Do not scan the whole account by default.

**Dispatch rule**: Most creative preview tools are L1 dispatcher-only (NOT L0 direct).
Always call them via `tool_execute(tool_name="ToolName", params={{...}})`.
If an L0 direct call returns "unknown tool", that's expected — retry via L1 dispatcher immediately.

1. Select top/final ad rows from ad-level or creative-level insights.
2. Normalize TikTok identities:
   - regular/manual ad: `ad_id`
   - upgraded Smart+ creative path: `ad_id` from `dimensions=["ad_id"]` rows where
     `campaign_automation_type=UPGRADED_SMART_PLUS_CREATIVE`
   - upgraded Smart+ landing/config path: `ad_id_v2` or `smart_plus_ad_id` from `dimensions=["ad_id_v2"]` rows where
     `campaign_automation_type=UPGRADED_SMART_PLUS`
   - never mix `ad_id` and `ad_id_v2` in one report request unless the MCP tool explicitly supports it
3. Read regular ad detail via **L1 dispatcher**: `tool_execute("ad_get", {{advertiser_id, filtering: {{ad_ids: [...]}}}})`. Request creative/material fields that expose image IDs, video IDs, Spark post IDs, playable URLs, thumbnails, cover images, and preview links when the tool schema permits them.
4. Read upgraded Smart+ ad detail via **L0 direct**: `smart_plus_ad_get`. Use `smart_plus_ad_ids` and batches of at most 50. Prefer Smart+ `creative_list`, `image_info`, `video_info`, `tiktok_item_id`, `landing_page_url_list`, and any returned preview URL fields.
5. If a row uses Smart Creative materials and regular/Smart+ ad detail only returns material references, record `structured_unavailable` for `/ad/aco/get/` because the official v2 mapping has no `new_name`.
6. For image IDs, call **L1 dispatcher ONLY**: `tool_execute("file_image_ad_info_get", {{advertiser_id, image_ids: [...]}})`. ⚠ This tool is NOT an L0 direct tool. Capture usable `image_url`, `thumbnail_url`, or `preview_url` values. Use image search only for discovery when IDs are not yet known. If the detail route succeeds but returns no URL fields, mark `asset_reference`.
7. For video IDs, call **L1 dispatcher ONLY**: `tool_execute("file_video_ad_info_get", {{advertiser_id, video_ids: [...]}})`. ⚠ This tool is NOT an L0 direct tool. Capture usable `cover_url` (`video_cover_url`), `thumbnail_url`, `video_url`, `playable_url`, or `preview_url` values. If the route succeeds but returns no URL fields, keep `asset_reference`.
8. For Spark Ads or TikTok item references, call **L1 dispatcher ONLY**: `tool_execute("tt_video_list_get", {{advertiser_id, page_size: 50}})`. ⚠ This tool is NOT an L0 direct tool. Search by item ID when supported; otherwise page through authorized posts only for the final candidate IDs. Capture `poster_url`, `preview_url`, carousel image URLs, or public/permitted post URLs.
9. For identity post references, call **L1 dispatcher**: `tool_execute("identity_video_info_get", ...)`, using identity context from `identity_get` (L0 or L1) when needed.
10. For upgraded Smart+ material-level diagnosis, use L0 direct `smart_plus_material_report_overview_run` and `smart_plus_material_report_breakdown_run` when report-level material rows are needed.
11. If L1 dispatcher tools still fail, use dispatcher discovery in this order: `ad`, `smart_plus`, `creative`, `file`, `identity`, `business`, `report`.

### HTML Embedding Contract

**Every resolved URL MUST be embedded in the HTML.** The preview URL IS the preview.
Never output bare text labels like "inline_image" or "asset_reference" in place of the actual image.

| Resolved Field | HTML Output |
|---|---|
| `video_cover_url` or `poster_url` | `<img src="{url}" alt="{name}" style="width:100%;aspect-ratio:9/16;object-fit:cover">` |
| `preview_url` (video) | `<a href="{url}" target="_blank">▶ Play video</a>` |
| `image_url` (carousel/upload) | `<img src="{url}" alt="{name}" loading="lazy">` |
| `spark_post_url` | `<a href="{url}" target="_blank">View on TikTok</a>` |
| `tiktok_item_id` only (no URL) | Text label with item_id + note "Spark Ad — URL not resolved" |
| Permission denied | Text label: "Permission denied" — do not drop the row |
| Tool unavailable | Text label: "Preview unavailable — {tool_name} not callable" |

**Verification**: Before marking a report as complete, check that at least one `<img>` tag
appears in the creative preview section of the HTML. A report with zero embedded images
in the preview section is incomplete.

## Field Retry Rules

TikTok MCP field names are strict. If `ad_get` or `adgroup_get` rejects a requested field:

- Read the accepted-field list from the error.
- Retry once with only accepted fields needed for the report.
- Record the rejected fields in the source artifact.
- Do not abandon the whole enrichment step just because one optional field was rejected.

For `ad_get`, prioritize these fields when accepted:

- `ad_id`, `ad_name`, `campaign_id`, `campaign_name`, `adgroup_id`, `adgroup_name`
- `operation_status`, `secondary_status`, `campaign_automation_type`
- `image_ids`, `video_id`, `tiktok_item_id`, `playable_url`
- `landing_page_url`, `landing_page_urls`, `page_id`, `catalog_id`, `product_set_id`, `sku_ids`
- `app_name`, `tracking_app_id`, `tracking_pixel_id`, `identity_id`, `identity_type`

For `adgroup_get`, prioritize these fields when accepted:

- `adgroup_id`, `adgroup_name`, `campaign_id`, `campaign_name`
- `operation_status`, `secondary_status`, `campaign_automation_type`
- `promotion_type`, `optimization_goal`, `billing_event`, `budget`, `budget_mode`
- `placements`, `placement_type`, `location_ids`, `age_groups`, `gender`, `interest_category_ids`, `actions`
- `app_id`, `pixel_id`, `conversion_window`

## Batch Failure Recovery

Media detail routes can fail the full batch because one referenced asset is not accessible. Handle that as
partial coverage:

1. Call `file_image_ad_info_get` or `file_video_ad_info_get` for the de-duplicated media IDs from final rows.
2. If the response says one or more IDs have insufficient permissions, write the failed IDs to
   `permission_denied_ids`.
3. Retry the same tool without the failed IDs.
4. Mark rows that depend only on failed IDs as `permission_denied` or `asset_reference`.
5. Continue resolving the rest of the rows and count only concrete URL/image evidence as preview coverage.

Do the same for Spark and identity post lookups: a supported empty response for a searched `tiktok_item_id` should
be stored as `spark_post_reference` or `supported_empty`, not as a failed report.

## MCP Parity Map

| Business API route | MCP route | Status | Notes |
| --- | --- | --- | --- |
| `/open_api/v1.3/ad/get/` | dispatcher `ad_get` | exact | Primary regular-ad detail source. |
| `/open_api/v1.3/smart_plus/ad/get/` | direct `smart_plus_ad_get` | exact | Primary upgraded Smart+ detail source. |
| `/open_api/v1.3/ad/aco/get/` | no v2 `new_name` | unavailable | Official mapping has no v2 tool for Smart Creative material references. |
| `/open_api/v1.3/file/image/ad/info/` | direct `file_image_ad_info_get` | exact | Resolve image media info and usable image URLs. |
| `/open_api/v1.3/file/video/ad/info/` | direct `file_video_ad_info_get` | exact | Resolve video media info and usable cover/video URLs. |
| `/open_api/v1.3/tt_video/list/` | direct `tt_video_list_get` | exact | Resolve Spark Ad post and carousel/video preview evidence. |
| `/open_api/v1.3/identity/video/info/` | direct `identity_video_info_get` | exact | Resolve a TikTok identity post when identity context is available. |
| `/open_api/v1.3/smart_plus/material_report/overview/` | direct `smart_plus_material_report_overview_run` | exact | Use for upgraded Smart+ material-level overview diagnostics. |
| `/open_api/v1.3/smart_plus/material_report/breakdown/` | direct `smart_plus_material_report_breakdown_run` | exact | Use for upgraded Smart+ material-level breakdown diagnostics. |

## Safety

- Do not store tracking URLs, click-tracking URLs, impression URLs, pixel scripts, authorization headers, tokens, or login/session metadata.
- Signed TikTok media URLs may expire. They may be stored only in source artifacts and HTML preview actions when returned by MCP and when they do not match the audit secret patterns.
- Do not print preview URLs in chat summaries. Return report paths and coverage numbers instead.
- If a usable preview URL contains a credential-like query parameter, set `preview_status` to `permission_denied` or `unavailable` and keep only non-sensitive reference IDs.
- Keep signed media URLs out of chat summaries even when they pass the audit. Use counts, statuses, and report paths.

## HTML Contract

For each final creative/ad row:

- `Preview` should render an inline image when `preview_image_url`, `thumbnail_url`, `cover_url`, or `image_url` is present.
- `Preview action` should link or expose a hover/focus action when `preview_action_url`, `video_url`, `playable_url`, `preview_url`, or `spark_post_url` is present.
- Rows with only `asset_reference`, `spark_post_reference`, or `creative_reference` must show `Unavailable` in the preview cell and show the reference ID in a diagnostic column or tooltip.
- Do not drop a row because preview enrichment fails.

## Status Mapping

Use exact statuses:

| Situation | Status |
| --- | --- |
| Inline thumbnail/cover/image URL available | `inline_image` |
| Only playable/video/preview action URL available | `action_url_only` |
| Spark post URL/permalink available | `spark_post_url` |
| Only asset/media ID available | `asset_reference` |
| Only Spark post ID available | `spark_post_reference` |
| MCP returns permission error | `permission_denied` |
| Tool route rejects the object type | `unsupported` |
| No callable route exists in the current MCP namespace | `structured_unavailable` |
| No eligible ad rows exist | `supported_empty` |
| Route succeeds but no preview fields exist | `unavailable` |

## Coverage Reporting

Write preview coverage into `validation_summary.json`:

```json
{
  "creative_preview": {
    "checked": 10,
    "with_preview": 5,
    "permission_or_reference_only": 5
  }
}
```

The numerator must include only `inline_image`, `action_url_only`, and `spark_post_url` rows. All other rows stay
visible in the HTML with `Unavailable` and a diagnostic status.
