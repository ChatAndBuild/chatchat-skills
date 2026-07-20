# MCP Workflows

Use these workflows after completing MCP initialization.

## Account Inspection

1. List accessible accounts or advertisers.
2. Fetch account entities and linked assets.
3. Fetch pages, identities, datasets, pixels, catalogs, apps, product sets, lead pages, creative portfolios, media assets, and Business Center relationships relevant to the platform.
4. For TikTok, use [tiktok-operation-map](tiktok-operation-map.md) and [tiktok-analysis-playbooks](tiktok-analysis-playbooks.md) to classify advertiser type from top-spend, landing/app, catalog/shop, app, and metric evidence.
5. Return scope, coverage, missing permissions, and recommended next action.

Expected output:

- account scope
- asset_inventory
- missing items
- abnormal bindings
- advertiser type label
- follow-up analysis path

## Read-First Delivery

1. Read target account and existing campaign structure.
2. Inspect required assets before building payloads.
3. Validate blocking errors, review status, dataset health, catalog health, app events, or identity/page availability.
4. Produce a paused create plan or update plan.
5. Execute only after explicit approval.

## Campaign Creation

1. Confirm platform, account, objective, budget, schedule, promoted object, and creative assets.
2. Ensure linked assets are available.
3. Create campaign paused.
4. Create ad group paused.
5. Create ad paused.
6. Run blocking-error or review checks.
7. Ask separately before activation.

## Product Or App Cold Start

Use this when the user only has a product page, store page, app page, or product brief and needs a same-day testing plan.

1. Extract the offer, product category, price point, claims, audience hints, conversion path, and required proof from the user-provided page or brief.
2. If a platform account or advertiser is provided, run `ensure_mcp_ready` and validate available pixel, app, catalog, identity, page, and creative prerequisites.
3. If no account is provided, produce a strategy-only brief and mark platform validation as `partial`.
4. Build a campaign brief with objective, promoted object assumption, event requirement, audience hypotheses, creative angles, budget split, and testing matrix.
5. If the user asks to launch, enter the read-first delivery workflow and create only paused or disabled objects after approval.

Expected output:

- campaign brief
- offer and selling-point summary
- audience hypothesis matrix
- creative angle matrix
- budget and test split
- launch-readiness checklist
- missing platform prerequisites

## Performance Review

1. Define period and comparison window.
2. Pull account or advertiser details.
3. Classify advertiser/user type before analysis when it was not explicitly supplied. For TikTok, follow the
   `user_type` evidence chain in [tiktok-analysis-playbooks](tiktok-analysis-playbooks.md) and write
   `user_type.json` before metric preset, metric probe, insight interpretation, or HTML generation.
   Reuse a fresh account-level user type cache when available instead of repeatedly pulling
   classification seed data for the same advertiser. Creative, ad, audience, activity, budget,
   bottleneck, landing/app, and performance diagnostics must still load `user_type.json` and
   `metric_preset.json` so their analysis uses the correct vertical metric lens.
4. Resolve metric preset, list the full metric set in Chinese and English, and ask the user for
   additions or adjustments. User-added metrics must pass one metric probe/data-pull test before
   they are saved to the account cache. Run metric probe when key fields or vertical metrics are uncertain.
5. Pull advertiser, campaign, ad group, and ad-level insights for current and comparison windows.
6. Add TikTok diagnostics: Smart+ reports, creative reports, audience breakdown, review info, landing/app evidence, pixel/app/catalog health, metric probe when key fields are absent, metric preset recommendation, targeted activities/changelog, and creative preview enrichment.
7. Use [vertical-metric-playbooks](vertical-metric-playbooks.md) and [vertical-report-templates](vertical-report-templates.md) for user-type-specific metrics, sections, and caveats.
8. Classify issues as scale, maintain, fix, reduce, pause, or measurement risk.
9. Return next actions with confidence and evidence.

Daily Pulse output should include anomaly flags, changed objects, delivery blockers, root-cause notes, and priority_actions.

Creative fatigue review should rank fatigue candidates, high-spend low-conversion watchlists, retention drop-offs, preview availability, refresh priority, and replacement recommendations. Use [creative-analysis](creative-analysis.md).

Audience, placement, geo, and device diagnosis should use [audience-optimization](audience-optimization.md) and explicit breakdown evidence before generic commentary.

Budget and bid recommendations should use [budget-and-bid-optimization](budget-and-bid-optimization.md) and remain approval-gated.

Measurement mismatch, missing value metrics, SKAN/SAN, modeled data, or W2A attribution questions should use [measurement-and-attribution](measurement-and-attribution.md).

Multi-level bottleneck diagnosis should explain whether the spend drop is at advertiser, campaign, ad group, ad, creative, identity, budget, review, tracking, or platform-limit level.

### Subagent Execution Lessons

For full/deep TikTok reports, use `mcp_subagent_executor` as a coordination pattern, not as a
separate platform client. The subagent makes the TikTok MCP call; the main session owns state,
raw-file recovery, normalization, validation, and audit.

Rules learned from live TikTok MCP report pulls:

- Formal report rows use direct `report_integrated_get` only. Do not route KPI, audience,
  comparison, `ad_v2`, or metric-probe pulls through L1 dispatcher.
- A subagent final status is advisory. The run can advance only after each planned source has
  either a `raw/*.json` file or a recoverable `mcp_tool_call_end` event.
- For large payloads, `function_call_output` may be truncated or invalid JSON. Recover from
  `mcp_tool_call_end.payload.result.Ok.content[0].text` instead.
- Use `recover_subagent_mcp_payloads.py --run-dir <run_dir>` as the default recovery path; it
  matches the session event arguments back to `mcp_tasks.jsonl` and writes missing raw files.
- Use generated `subagent_prompts/*.md` files for worker startup so each shard gets exact task
  boundaries without prompt-building overhead.
- Execute only `blocking_before_report` shards for the first audited report. Defer
  `optional_after_first_report` preview/activity-enrichment shards until the report exists or
  the user explicitly asks for enrichment.
- Each subagent must write and verify a non-empty planned `raw/*.json` immediately after every
  MCP call. If it cannot verify the raw file, stop the shard and recover instead of continuing.
- The main session may write recovered event payloads into `raw/*.json`; this does not violate
  the subagent approach because the platform API call still happened inside the subagent.
- If large event payload recovery is unavailable, relaunch only the missing source or page
  range with smaller pages. Use deterministic ranges and merge only after all pages exist.
- Use L1 dispatcher discovery only for non-report enrichment. If changelog/activity-log tools
  are not exposed by the active MCP server, write `structured_unavailable` with attempted tool
  names and exact unknown-tool errors.
- Rerun `workflow_runner.py` with the full original arguments after every recovery step. Do not
  call it without `--advertiser-id`, current dates, and previous dates, because that can produce
  a misleading blocked state.

## Landing Page And App Path Analysis

1. Pull ad-level or Smart+ ad-level report rows.
2. Enrich top spend objects with object details.
3. For TikTok, preserve the full regular ad, Smart+, upgraded Smart+, creative, ad group, app, catalog, shop, identity, and product evidence chain.
4. Extract landing, app store, deeplink, product, catalog, shop, creative asset, and unknown URL evidence separately.
5. Group spend, clicks, conversions, value, and ROAS by normalized URL, SKU, product, or app path when supported.
6. For ecommerce, include SKU-level or landing-page-level performance whenever catalog or product evidence exists.
7. Mark missing URL-level evidence as `partial`, not as zero.

Use [landing-page-and-funnel](landing-page-and-funnel.md) for destination evidence, URL canonicalization, W2A classification, and funnel proxy output.

## Cross-Account Rebuild

Use this when an account is restricted, ownership changes, or the user needs to recreate campaigns under a different advertiser or business context.

1. Confirm source account, destination account, object scope, and whether the user wants a plan only or approved execution.
2. Run `ensure_mcp_ready` and read source campaign, ad group, ad, Smart+, catalog, app, pixel, identity, page, product, creative, and file evidence.
3. Read destination account assets and permissions.
4. Build a portability matrix: reusable, needs sharing, needs recreation, blocked, unknown.
5. Generate a rebuild payload plan for campaigns, ad groups, ads, creatives, identities, catalogs, apps, and tracking dependencies.
6. Do not share, create, update, or activate anything until the user approves the exact operation.
7. Execute in stages when approved: prerequisite assets first, campaign structures second, ads third, validation fourth, activation last.
8. For TikTok, use [tiktok-validation-and-rebuild](tiktok-validation-and-rebuild.md) and write resumable records only after execution is approved.

Expected output:

- source entity map
- destination gap analysis
- asset reuse matrix
- rebuild payload plan
- blocked or non-portable items
- staged approval sequence
- resumable execution notes when execution is approved

## Advertiser Type Classification

Use recent top-spend evidence:

- campaign objectives
- ad group optimization goals
- promoted object type
- catalog/shop evidence
- app or store evidence
- landing URL evidence when available
- dataset, pixel, app event health

Return type, confidence, evidence, and metrics that are likely meaningful for that type.

## Reports

Use [report-contract](report-contract.md). For TikTok, also use [tiktok-report-runner](tiktok-report-runner.md). Reports should preserve:

- platform and account scope
- date range and timezone when known
- tools used
- coverage and degraded sources
- user type and evidence
- metric set and caveats
- activity/changelog context when available
- creative preview and retention enrichment when available
- top findings and action plan

Before returning a formal report, run the audit in [report-validation](report-validation.md), write `validation_summary.json`, write `report_audit.json`, and fix required failures or mark degraded coverage clearly.

When a source fails, use [error-cache-degradation](error-cache-degradation.md) to distinguish full, batch, partial, sampled, degraded, and failed states.
