# Report Validation

Use this reference for formal report QA before returning a report path.

## Required Audit

Run the local audit script after writing a formal HTML report:

```bash
python3 scripts/audit_creatiads_report.py \
  --run-dir build/creatiads_runs/<platform>_<account>_<period>_<depth>_<until> \
  --out build/creatiads_runs/<platform>_<account>_<period>_<depth>_<until>/report_audit.json
```

Fix required failures before returning the final answer. If a failure cannot be fixed because the MCP source is unavailable, keep the report only when the degraded source is explicitly recorded in `manifest.json`, `validation_summary.json`, and the HTML data-quality section.

## Required Checks

The report run must pass or explicitly explain:

- `manifest.json` parses and contains scope, period, depth, coverage, partial sources, degraded sources, and privacy redactions.
- `manifest.json` declares the account/ad account/advertiser ID, current window, comparison window when used, MCP
  server names or server aliases, tools called, validation status, and source files.
- Every `source_files` or `files` entry in `manifest.json` exists relative to the run directory.
- Every JSON file in the run directory and `sources/` parses.
- `user_type.json` exists for formal platform reports and was produced before `analysis_brief.json` and `report.html`
  when filesystem timestamps are available.
- Current and comparison source rows exist before rendering period-over-period deltas.
- TikTok formal reports record candidate-pool row counts and final selected row counts for campaign, ad group/ad
  set, ad, and Smart+ identities when those levels are in scope. Candidate pools should fetch up to 3000 rows per
  level when the MCP report route supports pagination.
- Required KPI fields are parseable numbers or explicitly marked `supported_empty`, `unsupported`, `permission_denied`, `rate_limited`, `not_queried`, or `partial`.
- HTML includes scope, user type or classification source, coverage state, KPI snapshot, drivers/findings,
  recommended actions, and data quality.
- HTML table CSS supports long names and URLs with `overflow-wrap:anywhere` and `word-break:break-word`.
- Creative/ad tables include a preview contract: inline preview when available, hover/focus action when a preview URL is available, and `Unavailable` when missing.
- Artifacts contain no tokens, authorization headers, OAuth callback secrets, MCP session metadata, script bodies from pixels, tracking URLs with credentials, or unauthorized account data.
- For the selected depth, no required source remains `not_queried` after a report rerun. Required sources must
  show an actual runtime status such as `ok`, `partial`, `supported_empty`, `permission_denied`, or `unsupported`.
- `partial_sources`, `supported_empty_sources`, `permission_denied_sources`, and `unsupported_sources` are not
  collapsed into `degraded_sources`; each class should be inspectable in `validation_summary.json`.

## Validation Summary

Write `validation_summary.json` for client-facing reports:

```json
{
  "status": "passed | passed_with_degradation | failed",
  "current_window_complete": true,
  "comparison_window_complete": true,
  "numeric_fields_parse": true,
  "row_counts": {},
  "preview_coverage": {
    "rows": 0,
    "with_preview": 0,
    "unavailable": 0
  },
  "degraded_sources": [],
  "partial_sources": [],
  "not_queried_sources": [],
  "privacy_redactions": []
}
```

For TikTok reports, include candidate-pool selection metadata:

```json
{
  "candidate_pools": {
    "campaigns": {"limit": 3000, "rows": 0, "final_selected": 0, "sort_keys": ["spend"]},
    "adgroups": {"limit": 3000, "rows": 0, "final_selected": 0, "sort_keys": ["spend"]},
    "ads": {"limit": 3000, "rows": 0, "final_selected": 0, "sort_keys": ["spend"]},
    "smart_plus_ads": {"limit": 3000, "rows": 0, "final_selected": 0, "sort_keys": ["spend"]}
  }
}
```

When upgraded Smart+ rows are present, also include routing diagnostics:

```json
{
  "smart_plus_routing": {
    "report_detection_fields": ["dimensions", "campaign_automation_type", "ad_id_v2", "smart_plus_ad_id"],
    "creative_path": {
      "dimension": "ad_id",
      "campaign_automation_type": "UPGRADED_SMART_PLUS_CREATIVE",
      "identity_meaning": "creative_id",
      "rows": 0
    },
    "landing_path": {
      "dimension": "ad_id_v2",
      "campaign_automation_type": "UPGRADED_SMART_PLUS",
      "identity_meaning": "smart_plus_ad_id",
      "rows": 0,
      "unique_smart_plus_ad_ids": 0,
      "detail_batches": 0
    }
  }
}
```

The audit handoff should fail or mark the report degraded when an upgraded Smart+ account has creative rows but no
attempted `ad_id_v2` landing path, unless the MCP route explicitly returns `unsupported` or `permission_denied`.

Include a `source_status` or equivalent structured list when any source is partial or unavailable:

```json
{
  "source_status": [
    {
      "name": "audience_country",
      "status": "ok | partial | supported_empty | unsupported | permission_denied | rate_limited | not_applicable | not_queried",
      "rows": 0,
      "tool": "MCP tool name when known",
      "reason": "short runtime explanation"
    }
  ]
}
```

Do not collapse `unsupported`, `supported_empty`, `permission_denied`, `rate_limited`, and `partial` into one
generic degraded bucket. The distinction is part of the report contract.

For TikTok `full` or `deep` reports, include coverage details:

```json
{
  "coverage": {
    "audience": {
      "country": 0,
      "age_gender": 0,
      "placement": 0,
      "device": 0
    },
    "creative_preview": {
      "checked": 0,
      "with_preview": 0,
      "permission_or_reference_only": 0
    },
    "activities": {
      "rows": 0
    },
    "landing_app_paths": {
      "rows": 0
    }
  },
  "partial_sources": [],
  "supported_empty_sources": [],
  "permission_denied_sources": [],
  "unsupported_sources": [],
  "not_queried_sources": []
}
```

## Comparison Policy

Render period-over-period cards only when current and comparison windows are both present and equal length. If comparison is missing or partial, render single-period KPIs and state the comparison gap.

For `daily` and `weekly` reports, previous-period data is expected by default. If it is unavailable, the report
must show a single-period state, mark `comparison_eligible: false`, and explain the missing comparison source in
`validation_summary.json` and the HTML data-quality section.

## HTML Section Policy

Formal reports should include these blocks, adapted to the user language:

- coverage header: scope, user type/classification source, metric set, coverage, and limits
- executive summary
- KPI snapshot or KPI change
- drivers/findings with evidence and confidence
- winners/watchlist/bleeders when entity-level data is available
- creative/ad table with preview contract when creative or ad rows are present
- landing, app, W2A, SKU, catalog, shop, or path notes when those sources are in scope
- audience, placement, device, or geo notes when breakdowns are in scope
- measurement risks and data gaps
- recommended actions with approval requirements
- data quality and provenance

If a section is not applicable, keep a concise note rather than silently omitting the topic.

## Preview Policy

Decide final report rows from insights before fetching previews. Enrich only those rows. Signed media URLs may expire; store them only when they are needed for report inspection and do not include secrets or tracking credentials.

For TikTok, a row counts toward `preview_coverage.with_preview` only when `sources/creative_previews.json` contains a concrete URL/image field such as `preview_image_url`, `thumbnail_url`, `cover_url`, `image_url`, `video_url`, `playable_url`, `preview_url`, `permalink_url`, or `spark_post_url`. Non-URL references remain useful diagnostics but must not be counted as preview coverage.

The audit may pass with partial preview coverage when every final ad row is present and each row has a precise
status. It must not pass a report where creative previews were never queried for a depth that requires them.

## TikTok Full Report QA

Before returning a TikTok `full` report:

- Confirm `user_type.json` was generated before `analysis_brief.json` and `report.html`.
- Confirm audience files exist and have row counts or explicit `supported_empty` / `unsupported` status.
- Confirm `sources/ad_details_*.json` and `sources/adgroup_details_*.json` exist or are explicitly unavailable.
- Confirm `sources/creative_previews.json` has one row per final report ad row.
- Confirm `sources/creative_retention.json` or `sources/creative_retention_raw.json` exists when creative fatigue is discussed.
- Confirm activities were either parsed from changelog download rows or classified as `supported_empty`,
  `unsupported`, or `permission_denied`.
- Confirm landing/app paths state whether they contain concrete URLs, promoted-object evidence, pixel/app IDs, or
  only partial object detail.
