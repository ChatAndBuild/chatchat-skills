# TikTok Validation And Rebuild

Use this reference for prelaunch risk checks, multi-level bottleneck diagnosis, and cross-account rebuilds.

## Prelaunch Risk Check

Run `validate_promoted_object` when a TikTok campaign, ad group, app, website, pixel, catalog, identity, or promoted object is about to be launched or updated.

Run `validate_creative` when an ad creative, image, video, landing URL, tracking app, or asset relationship is being attached to a delivery object.

Run `validate_ad_link` when an existing ad group or ad is suspected of having an invalid page/app/pixel/catalog/identity/creative relationship.

### Validation Steps

1. Read advertiser state.
2. Read campaign/ad group/ad state when object IDs exist.
3. Read relevant app, pixel, catalog, product set, identity, lead page, creative asset, and landing URL evidence.
4. Run the narrowest validation tool available.
5. If no single validation tool exists, synthesize a relationship check from the source reads and mark the result as `partial`.

### Output

```json
{
  "go_no_go": "go | no_go | partial",
  "failed_points": [],
  "missing_assets": [],
  "abnormal_bindings": [],
  "warnings": [],
  "next_safe_fix": [],
  "write_required": false
}
```

## Multi-Level Bottleneck Diagnosis

Use this when spend drops, delivery stops, or the user asks where the account is stuck.

### Trace Order

1. Advertiser status, balance, account budget, account limits, and permission state.
2. Campaign status, budget, objective, optimization goal, schedule, and review state.
3. Ad group status, budget, bid, targeting, promoted object, app/pixel/catalog identity, and review state.
4. Ad status, creative review, identity binding, landing/app path, and creative asset availability.
5. Report trend by day and by level.
6. Recent activity/changelog for changed top objects.
7. Platform limitations, unsupported metrics, and rate/permission errors.

### Root-Cause Labels

- `account_limit`
- `balance_or_billing`
- `campaign_budget`
- `adgroup_budget_or_bid`
- `schedule`
- `review_or_policy`
- `status_disabled`
- `creative_invalid`
- `identity_or_page_binding`
- `promoted_object_invalid`
- `tracking_or_measurement`
- `audience_or_targeting`
- `platform_limit`
- `unknown_partial`

Return the lowest failing layer, evidence, confidence, and next diagnostic or fix step.

## Cross-Account Rebuild

Use this when an advertiser is restricted, ownership changes, assets must move, or a campaign structure must be recreated in another advertiser.

### Plan-Only First

Default to a plan. Do not share, create, upload, update, duplicate, or activate until the user approves a specific staged operation.

### Source Export

Read source:

- advertiser account details
- campaigns and Smart+ campaigns
- ad groups and Smart+ ad groups
- ads and Smart+ ads
- identity and posts
- apps and app events
- pixels and custom conversions
- catalogs, feeds, products, product sets, video packages
- creative portfolios, images, videos, thumbnails, music, and files
- landing/app URL evidence
- review/blocking errors

### Destination Gap Analysis

Read destination:

- advertiser account details and permissions
- available identities
- apps, pixels, custom conversions, catalogs, products, creative assets, lead pages, and Business Center relationships
- upload/share support for missing media or creative assets

Classify every dependency:

- `reusable`
- `needs_sharing`
- `needs_upload`
- `needs_recreation`
- `blocked`
- `unknown`

### Rebuild Plan

Create a staged payload plan:

1. prerequisite assets
2. tracking and promoted objects
3. campaigns
4. ad groups
5. ads and creative bindings
6. validation
7. optional activation

Each stage must include:

- input objects
- destination IDs
- payload summary
- validation command or MCP route
- rollback or resume note
- approval requirement

### Resumable Execution Record

When execution is approved, write a resumable record in the run directory:

- `rebuild_plan.json`
- `rebuild_state.json`
- `rebuild_failures.json`
- `rebuild_approvals.json`

Do not store secrets or MCP session metadata.
