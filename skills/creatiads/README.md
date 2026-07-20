# Creatiads

Creatiads is a TikTok MCP-first advertising orchestration skill for reporting,
diagnostics, optimization, and guarded operations. It routes platform data
access through the remote TikTok MCP server, keeps local scripts compute-only,
and produces auditable outputs for performance analysis and client-facing
reports.

## What It Does

Use Creatiads for TikTok advertising work such as:

- Listing advertising accounts, campaigns, ad groups, and ads.
- Finding best or worst performing campaigns and ads.
- Producing daily pulse reports, weekly reports, and formal HTML reports.
- Classifying advertiser verticals and selecting vertical-aware metric presets.
- Diagnosing performance, audience, creative fatigue, landing page, app path,
  budget, bid, measurement, attribution, review, and delivery issues.
- Working with TikTok, Smart+, TikTok One, GMV Max, Product GMV Max,
  TikTok Shop reports, Pangle, Spark Ads, carousel ads, catalog ads, shop ads,
  pixels, audiences, product catalogs, and creative previews.
- Planning cross-account rebuilds or guarded campaign operations.

The skill supports 13 advertiser types: ecommerce, short drama, utility or W2A,
casual game, midcore or hardcore game, novel, social, entertainment,
financial leads, search arbitrage, earnings or offerwall, regulated high risk,
and agency or mixed accounts.

## Required MCP Server

Creatiads requires the TikTok MCP server before any platform API operation.

Default server:

```text
Name: tiktok-mcp
URL:  https://business-api.tiktok.com/open_mcp/tt-ads-mcp-layer
```

Before running account, report, or operation workflows, the agent should:

1. Check whether an MCP server already exists for the same URL.
2. Add the server if it is missing.
3. Start OAuth login if authorization is required.
4. Avoid printing tokens, authorization headers, callback secrets, or MCP
   session metadata.
5. Stop with a structured unavailable result if TikTok MCP is not callable.

## Core Workflow

Creatiads uses a user-type-first report workflow. For any report, diagnosis, or
analysis task, the agent follows this sequence:

```text
1. MCP READY     -> Ensure tiktok-mcp is initialized and authorized
2. ACCOUNT INFO  -> Pull advertiser timezone, currency, and status
3. CLASSIFY SEED -> Pull minimal current-window evidence for classification
4. USER TYPE     -> Write user_type.json
5. METRIC PRESET -> Write metric_preset.json from user_type.json
6. REPORT DATA   -> Pull current and previous formal reports
7. ENRICHMENT    -> Pull audiences, creative previews, landing paths, activity
8. HTML + AUDIT  -> Produce analysis, HTML report, and audit artifacts
```

The classification and metric preset phases must happen before formal report
data pulls. This prevents generic metrics from being used for accounts whose
business models need different interpretation.

## Data Plane Rules

TikTok MCP is the default data plane.

- Use direct MCP reporting for formal KPI, comparison, audience, ad v2, and
  metric-probe rows.
- Use the L1 dispatcher for tools that are not exposed as direct MCP functions.
- Do not assume a tool is unavailable just because it is not listed as a direct
  function.
- Record unavailable, permission-denied, rate-limited, partial, degraded, and
  unsupported sources explicitly.
- Do not use non-MCP data sources unless the user explicitly requests an
  external fallback.

## Scripts Are Compute-Only

Local Python scripts do not create MCP clients, perform OAuth, or call platform
APIs. The agent performs MCP calls and writes raw or normalized data for scripts
to process.

Important scripts include:

- `scripts/build_mcp_pull_plan.py` - creates pull plans and MCP task files.
- `scripts/classify_user_type.py` - classifies advertiser verticals.
- `scripts/metric_probe.py` - builds metric presets and metric probes.
- `scripts/run_report.py` - assembles report data and HTML output.
- `scripts/audit_creatiads_report.py` - validates report artifacts.
- `scripts/creative_enrichment.py` - derives creative previews and retention.
- `scripts/audience_analysis.py` - analyzes audience breakdowns.
- `scripts/landing_app_analyzer.py` - canonicalizes landing and app paths.
- `scripts/activity_analysis.py` - normalizes changelog data.
- `scripts/finalize_workflow_run.py` - finalizes workflow state and audit.

## Report Outputs

Substantive reports should materialize data under:

```text
build/creatiads_runs/<platform>_<account_or_advertiser>_<period>_<depth>_<until>/
```

Formal reports should include, at minimum:

- Status bar with the overall account state and reason.
- KPI snapshot comparing current and previous periods.
- Campaign leaderboard ranked by spend with CPA or equivalent efficiency cues.
- Audience breakdown by country, age and gender, placement, and platform.
- Creative preview section with real image tags and clickable links.
- Activity changelog with budget, bid, targeting, and status changes.
- Prioritized next actions with P0, P1, and P2 recommendations.
- Data quality table with source status, row counts, and method notes.

## Safety Model

Creatiads is read-first by default.

For create, update, activate, delete, share, budget, bid, or status changes, the
agent should:

1. Read the target object first.
2. Summarize the intended payload and risk.
3. Ask for explicit user approval before acting.
4. Create new campaigns, ad groups, and ads in paused or disabled state by
   default.
5. Treat activation as a separate approval step.

## Package Structure

```text
creatiads/
|-- SKILL.md
|-- README.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- mcp-initialization.md
|   |-- tiktok-report-runner.md
|   |-- report-contract.md
|   |-- report-validation.md
|   `-- ...
`-- scripts/
    |-- build_mcp_pull_plan.py
    |-- workflow_runner.py
    |-- run_report.py
    |-- audit_creatiads_report.py
    `-- ...
```

## Example Prompts

```text
Generate a standard weekly TikTok ads report for advertiser 7444033053753835536
from 2026-06-15 to 2026-06-21, compared with 2026-06-08 to 2026-06-14.
```

```text
Analyze creative fatigue for this TikTok advertiser and identify which ads
should be scaled, refreshed, or paused.
```

```text
Diagnose the audience and budget allocation for my TikTok campaigns and
recommend what to adjust next.
```

```text
Prepare a Product GMV Max report for this TikTok Shop account and explain which
products, shops, and campaigns are driving the change.
```

## Notes

- Read `references/mcp-initialization.md` before platform API work.
- Read `references/tiktok-report-runner.md` before TikTok report generation.
- Read `references/gmv-max-reporting.md` for GMV Max, Product GMV Max, and
  TikTok Shop reports.
- Read `references/report-contract.md` and
  `references/report-validation.md` before generating or auditing HTML reports.
- See `references/copyright-notice.md` for the copyright notice.
