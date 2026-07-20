# tiktok-optimization-advisor

Mid-flight performance evaluation and optimization tool for active TikTok campaigns. An enterprise activator says "evaluate the campaign performance and recommend how to further optimize it" — the skill pulls live data, measures performance against KPI goals and vertical benchmarks, and returns a prioritized list of optimization actions ordered by expected impact.

## Overview

This Skill solves the mid-flight optimization problem for enterprise activation teams: given an active TikTok campaign, it determines what is underperforming and what to change, right now. It pulls live campaign, ad group, and creative data, assesses it against the client's KPI goals and vertical benchmarks, and produces an ordered set of optimization actions.

Each action is tagged as either **MCP-executable** (the TikTok for Business MCP can implement it directly) or **manual** (requires human action). The activator can act on the list themselves or hand MCP-executable items back to the MCP to implement immediately.

Setup diagnostics are not a standalone audit — they surface only when a structural issue is the root cause of an observed performance problem.

## Target platform

- TikTok for Business Agentic Hub / TikTok for Business MCP-compatible AI agents.
- No additional platform restrictions. The skill is delivered as a standard SKILL.md package; the bundled MCP server (`src/`) requires a Node.js runtime (see Prerequisites) only if you self-host the tools.

## Prerequisites / Dependencies

- **Agent / MCP:** This skill is designed to run against the **TikTok for Business MCP**. It does not require any other MCP or agent. The bundled `src/` MCP server is an optional self-hosted implementation of the five read tools listed below; if you use it instead of the TikTok for Business MCP, point your orchestrator at its endpoint (see Quick Start).
- **Account access:** TikTok Ads Manager account with active campaign access.
- **Runtime (only if self-hosting the bundled server):** Node.js >= 18.
- **Permissions:** read access to campaign, ad group, ad/creative, and reporting endpoints.
- **Environment variables:** `TIKTOK_ACCESS_TOKEN` and `TIKTOK_ADVERTISER_ID` must be set.

## Quick Start

If you are consuming this skill through the TikTok for Business MCP, no setup is required — the orchestrator loads `SKILL.md` and invokes the MCP tools directly.

To run the optional bundled MCP server locally:

```bash
npm install
npm start
```

The server starts on `http://localhost:3000` by default. Configure your AI orchestrator to connect to this endpoint.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TIKTOK_ACCESS_TOKEN` | Yes | — | TikTok Ads API access token |
| `TIKTOK_ADVERTISER_ID` | Yes | — | Default advertiser ID |
| `PORT` | No | `3000` | Server port for the bundled MCP server |

## Invocation

This skill is invoked automatically by the AI orchestrator based on the `description` field in `SKILL.md`. Representative trigger phrases:

- "evaluate the campaign", "evaluate campaign performance"
- "optimization recommendations", "recommend how to optimize"
- "why is my campaign underperforming", "what changes should I make"
- "mid-flight evaluation", "campaign health check"
- "low CTR", "low delivery", "too expensive", "creative fatigue"
- "vertical benchmarks for TikTok", "campaign isn't hitting goal"

## MCP Tools Exposed

See [`schema/tools_schema.json`](schema/tools_schema.json) for the full tool definitions.

| Tool | Purpose |
|------|---------|
| `tiktok_list_campaigns` | List active campaigns for an advertiser |
| `tiktok_get_reporting` | Pull campaign, ad group, and creative-level metrics |
| `tiktok_get_campaign_details` | Retrieve campaign-level configuration and settings |
| `tiktok_get_adgroup_details` | Retrieve ad group targeting, bidding, and budget settings |
| `tiktok_get_ad_details` | Retrieve ad and creative configuration details |

## Output Structure

Every evaluation produces three sections in this order:

1. **Performance Summary** — a 3–5 sentence assessment (pacing, KPI vs. goal, top creative signal) with a compact data table comparing actuals to goals and vertical benchmarks.
2. **Optimization Actions** — the primary deliverable. Up to 7 actions ordered by expected impact, each with what to do, where, why it matters, root cause (if structural), how to implement, and an execution tag (🤖 MCP-executable or 👤 Manual).
3. **Supporting Data** — only the tables relevant to the actions above.

Output is delivered as a structured list in chat, a **docx** document, or a **pptx** deck — the activator's choice.

## Limitations and caveats

- Recommendations are advisory; the skill never executes a write or budget change on its own. MCP-executable actions still require the activator (or the TikTok MCP, with confirmation) to run them.
- Vertical benchmarks are directional context, not guaranteed targets. Verticals not covered in `reference/recommendation-playbooks.md` fall back to objective- and audience-based passes only.
- Reporting is only as current as the TikTok API allows; very recent in-flight data may lag.
- The bundled `src/` server exposes read-only tools; it does not implement write operations.

## Common errors and troubleshooting

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| `401 / authentication failed` | Missing or expired `TIKTOK_ACCESS_TOKEN` | Regenerate the token in TikTok Ads Manager and reset the env var |
| Empty campaign list | Wrong `TIKTOK_ADVERTISER_ID` or no active campaigns | Confirm the advertiser ID and that campaigns are live |
| No data returned for a date range | Date range outside the campaign's flight | Use a range within the campaign start/end dates |
| Server will not start | Node.js < 18 | Upgrade to Node.js 18 or later |

If no data is returned for a requested metric, the skill states this explicitly rather than guessing.

## Directory Structure

```
tiktok-optimization-advisor/
├── SKILL.md                    # Main skill file (YAML frontmatter + instructions)
├── README.md
├── reference/                  # Supporting reference material (loaded on demand)
│   ├── recommendation-playbooks.md
│   ├── benchmarks.md
│   └── sources.md
├── schema/
│   └── tools_schema.json       # MCP tool definitions
├── src/                        # Optional self-hosted MCP server
│   ├── index.js
│   └── handlers/
└── package.json
```

## Relationship to Other Skills

| Use case | Skill to use |
|----------|-------------|
| Pure performance snapshot (no recommendations) | `tiktok-midflight-report` |
| Pre-launch setup audit | `tiktok-setup-bestpractices` |
| "Evaluate performance and tell me what to change" | **`tiktok-optimization-advisor`** |
| Post-campaign wrap report | `tiktok-campaign-eval` |

## Contact information

Maintained by the Innovid / SAM engineering team. For support inquiries or to report issues, contact the developer email provided in the Agentic Hub upload form (Developer Contact Email).
