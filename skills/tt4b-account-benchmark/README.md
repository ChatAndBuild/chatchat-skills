# TT4B Account Benchmark

> **Hackathon track:** Analysis & Diagnosis — Performance Readout & Campaign Diagnosis  
> **Skill version:** 0.3.0 | Grains: Campaign · Ad Group · Ad

An AI skill that turns raw TikTok Ads reporting data into a **same-advertiser, same-objective, same-grain performance benchmark** — giving advertisers an instant, data-backed answer to "is this Campaign/Ad Group/Ad actually performing well compared to the rest of my account?"

---

## Why This Matters

Advertisers routinely misread campaign performance because they lack a proper baseline. A CPM of $3 could be excellent for a brand-awareness objective and poor for a conversion campaign in the same account. Existing dashboards show absolute numbers with no within-account context.

**This skill solves the baseline problem:**

1. Fetches real report data via `tt-ads` MCP — no synthetic substitutes, no fabricated numbers.
2. Restricts the benchmark pool to the **same advertiser + same objective + same grain** — apples-to-apples only.
3. Runs deterministic local computation (P25 / P50 / P75 + percentile rank) via bundled local scripts — Node.js first, Python fallback, no LLM math, fully reproducible.
4. Surfaces conclusions in advertiser-facing language: "CPC is better than 75% of comparable Campaigns" or "CPA is worse than 88% of comparable Campaigns" rather than raw percentile numbers.

---

## What It Does

The skill covers three use modes in a single workflow:

| Mode | Example Prompt |
|---|---|
| **Single-object benchmark** | "Is this campaign's CPA better or worse than my account baseline?" |
| **Account overview with mandatory benchmark** | "How did my account perform over the last 7 days?" |
| **Candidate discovery** | "Find my highest-CVR ads and check if they're actually strong vs. the account." |

All three modes use the same same-objective, same-grain benchmark pool. Account overview is not a plain weekly readout: it must include an account benchmark in the same response. Discovery ranks candidates first, then benchmarks each one — no shortlist without evidence. By default, every readout shows both **Winners** and **Draggers** so advertisers see what is working and what is pulling the account down.

Every final answer must visibly contain a bottom-line judgment, a benchmark table, a benchmark verdict, next steps, and a compact scope appendix. For Chinese output, headings are Chinese-first: `结论先说`, `核心对比`, `基准结论`, `下一步建议`, `附录：基准范围`. A response that only gives account recap, WoW trend, or key campaigns without benchmark evidence is incomplete.

---

## Using Inside tt4b-skill-kit

Inside a broader `tt4b-skill-kit`, this skill is the atomic **relative-performance judge**:

| User intent | Best skill |
|---|---|
| "Show me the raw numbers / pull a report" | `tt4b-get-performance-report` |
| "Is this good vs. my own account baseline?" | `tt4b-account-benchmark` |
| "Why is this not spending / rejected / unhealthy?" | `tt4b-diagnose-campaign-health` |
| "Move budget from weak campaigns to strong ones" | `tt4b-optimize-budget` |

This skill triggers whenever the user asks whether performance is good, strong, weak, better/worse than the account, above/below account baseline, or whether a high-CVR / low-CPA / high-scale object is truly worth trusting. It also works as a follow-up after another reporting skill has already pulled data: once the user asks "so is that actually good?", switch from raw reporting to benchmark logic.

The skill is read-only. It does not diagnose delivery root cause, execute budget changes, or replace campaign-management skills.

If the broader kit is not installed, the skill does not stop just because a sibling route is unavailable. It can still provide limited read-only reasoning from `tt-ads` report fields, while clearly stating when a full report export, delivery-health diagnosis, or write-action workflow requires the matching skill.

---

## Prompt Cookbook — 不知道 benchmark 时怎么问

Users do not need to say "benchmark." Any prompt asking whether performance is good, reliable, scalable, or strong versus the account will trigger this skill.

| Intent | 中文 prompts | English prompts |
|---|---|---|
| Single object quality | `这条 campaign 还行吗？` `这个广告表现咋样？` | `Is this campaign actually doing well?` `Is this ad good compared with my account?` |
| Worth scaling | `这个广告值不值得继续加钱？` `这条素材能不能放量？` | `Is this ad worth scaling?` `Can this creative scale, or is it just lucky?` |
| Small-sample risk | `这个高 CVR 素材靠谱吗？` `这是不是样本太少的假象？` | `Is this high-CVR creative real or just small-sample noise?` `Can I trust this result?` |
| Pick winners | `帮我找最近真正值得放大的广告。` `这些 campaign 哪个更靠谱？` | `Find the ads that are truly worth scaling.` `Which campaign is genuinely stronger?` |
| Account readout | `最近账户哪里拖后腿？` `过去 7 天账户表现到底好不好？` | `What is dragging down my account performance?` `How good was my account performance last week?` |
| Objective-aware judgment | `Brand Awareness 没转化是不是差？` `Traffic campaign CPA 高要不要停？` | `This awareness campaign has zero conversions. Is that bad?` `This traffic campaign has high CPA. Should I judge it by CPA?` |
| Route elsewhere | `为什么没花出去？` → diagnosis · `帮我挪预算。` → optimization | `Why is this campaign not spending?` → diagnosis · `Move budget to the winners.` → optimization |

Mixed-language prompts also work: `这个 high CVR creative 靠谱吗？`, `这个 ad worth scaling 吗？`, `帮我找 truly strong 的素材。`

---

## End-to-End Flow

```text
User prompt
    │
    ▼
[0] Execution preflight — tt-ads MCP available? auth valid?
    │
    ▼
[1] Resolve advertiser context — explicit advertiser_id or BC → advertiser lookup
    │
    ▼
[2] Interactive intake — target object & window known?
    │   No → pull cost-active list for that advertiser → skill selects highest-spend primary target
    ▼
[3] Resolve objective & metric profile — objective_type → primary metrics for this goal
    │
    ▼
[4] Pull analysis report — report_integrated_get (BASIC, one target entity)
    │
    ▼
[5] Pull benchmark report — same objective / grain / window, page through all rows
    │   Optional Smart+ material enrichment → smart_plus_material_report_overview_run
    ▼
[6] Local benchmark compute — scripts/compute-account-benchmark.mjs or scripts/compute-account-benchmark.py
    │   → median, P25/P50/P75, percentile rank, sample-size check
    ▼
[7] Render result — reader-first narrative with single-grain Winners + Draggers:
        结论先说 → Winners/Draggers tables → 核心对比 → 基准结论 → 下一步建议 → 附录：基准范围
```

---

## Sample Output

```text
Campaign Benchmark — Last 7 Days

结论先说
- [Summer Prospecting](https://ads.tiktok.com/i18n/manage/campaign?...) 表现强：CPA 好于 82% 的可比 Campaign。
- Spend $2,450.00；Conversions 52；CVR 2.1%。

Winners（表现好）
这些 Campaign 在规模和转化效率上都高于账户水位。
| Campaign | Status | Spend | Conversions | CPA | CVR | Benchmark waterline | 定位 |
|---|---|---:|---:|---:|---:|---|---|
| [Summer Prospecting](https://ads.tiktok.com/i18n/manage/campaign?...) | ENABLE | $2,450.00 | 52 | $47.12 | 2.1% | CPA better than 82% of comparable Campaigns | Efficient scale winner |

Draggers（拖后腿）
这些 Campaign 处在较弱账户水位，且消耗规模足以影响目标桶结果。
| Campaign | Status | Spend | Conversions | CPA | CVR | Benchmark waterline | 定位 |
|---|---|---:|---:|---:|---:|---|---|
| [Broad Retargeting](https://ads.tiktok.com/i18n/manage/campaign?...) | ENABLE | $1,980.00 | 7 | $282.86 | 0.6% | CPA worse than 91% of comparable Campaigns | Current dragger to review |

核心对比
| 指标 | 当前对象 | 中位数 | 相对位置               | 业务判断         |
|---|---:|---:|---|---|
| CPA  | $47.12   | $96.40                | 好于 82% 的可比 Campaign | 转化效率强       |
| CVR  | 2.1%     | 1.4%                  | 好于 71% 的可比 Campaign | 点击质量高于账户水位 |

基准结论
[Summer Prospecting](https://ads.tiktok.com/i18n/manage/campaign?...) 是高水位 Campaign：CPA 好于 82% 的可比 Campaign，转化量高于 76% 的可比 Campaign。

下一步建议
- 以下建议基于报表数据，执行前请结合实时投放状态确认。

附录：基准范围
广告主：Example account (123) · 窗口：2026-06-08 → 2026-06-14 · 粒度：Campaign · 目标：WEB_CONVERSIONS · 基准池：18 个有消耗 Campaign
```

---

## Objective-Aware Metric Selection

The skill automatically maps `objective_type` to the right primary metrics — no manual configuration needed:

| Objective | Primary Benchmark Metrics |
|---|---|
| `WEB_CONVERSIONS` | CPA, CVR, CPC, CTR |
| `PRODUCT_SALES` | CPA, CVR, CPM, spend |
| `APP_PROMOTION` | CPA (install), CVR, CPC |
| `TRAFFIC` | CPC, CTR, CPM, clicks |
| `REACH` | CPM, impressions, frequency |
| `VIDEO_VIEWS` | CPV, 2s/6s view rate, completion |
| `LEAD_GENERATION` | CPL, CVR, CTR |

When objectives are mixed within an account, the skill splits benchmark output into objective buckets rather than blending CPA/CVR/CPM conclusions across incompatible goals.

---

## Smart+ Material Enrichment

The user-facing benchmark has only three grains: Campaign, Ad Group, and Ad. When the user asks
about "素材" / creative, the main benchmark uses Ad grain.

- For Smart+ Campaigns, `smart_plus_material_report_overview_run` may be used as optional
  enrichment to explain material contribution behind Ad-level winners or draggers.
- The enrichment aggregates by `main_material_id` and derives CPA / CVR / CTR / CPM locally from
  summed numerators.
- The main benchmark remains Ad-level. `creative_id`, Smart+ IDs, and material IDs are descriptive
  context; Ad-grain object names are not linked to Ads Manager.
- If the material tool is unavailable, the Ad-level benchmark remains the main result; avoid
  material-level claims.

---

## Candidate Discovery

For requests like "find my high-CVR creatives" or "which ads are underperforming":

1. Ranks candidates by the user's requested lens (CVR, CPA, scale)
2. Applies **adaptive evidence tiers** from the same benchmark pool — a 1-conversion ad cannot enter the top recommendation bucket regardless of CVR
3. Benchmarks each shortlisted candidate at the same grain against cost-active peers
4. Outputs both Winners and Draggers by default — not only the best-looking objects
5. Attempts read-only status lookup for each surfaced candidate and relevant parent object before calling it scalable or worth watching
6. Flags disabled candidates separately: "performance looked strong but the object is currently stopped"

If status tools are unavailable, the skill explicitly says so — it does not leave status as a casual "check later" caveat.

---

## Real Data Only

This skill runs on real `tt-ads` MCP data. It will not fabricate or substitute example values. If auth or advertiser access is unavailable, the skill surfaces the real blocker — that is the correct test result.

All computation runs locally on raw JSON returned by the MCP. The bundled scripts make no external network calls.

Output language follows the user's prompt. Chinese prompts receive Chinese conversation summaries and a Chinese `summary.md`; English prompts receive English. Saved `result.json` and `manifest.json` remain structured machine-readable artifacts regardless of language.

When saving artifacts, the conversation must already carry the full conclusion before listing file links. For ranked outputs such as "热门 adg", the chat answer names the overall winner, scale leader, efficiency candidate, main draggers, key caveat, benchmark scope, and compact metrics — then lists the file links.

---

## Prerequisites

- Node.js 18+ preferred, or Python 3.9+ as the bundled fallback runtime
- Claude, Codex, or another compatible agent host with skill/file support
- `tt-ads` MCP or the kit `tt-ads-mcp` dispatcher with advertiser and BASIC reporting access
- Optional Smart+ material enrichment: `smart_plus_material_report_overview_run` in the same MCP

If auth fails in Codex:

```bash
codex mcp login tt-ads
```

---

## Install

Copy the skill folder into your host's skills directory:

| Host | Path |
|---|---|
| Codex | `~/.codex/skills/tt4b-account-benchmark/` |
| Claude | `~/.claude/skills/tt4b-account-benchmark/` |
| Compatible agent host | The host's configured skills directory |

---

## Usage Examples

**Benchmark a known Campaign:**

```text
Is this campaign's CPC better or worse than the account baseline? Campaign Summer Sale (7412345678901), last 7 days.
```

**Cold-start (no ID known):**

```text
帮我找一下可用账户和最近有消耗的 Campaign，我选一个跑 benchmark。
```

**Account overview:**

```text
7514225548958957584 分享下我账号最近一周的表现
```

Expected: summarize the last 7 complete days, then in the same response show account benchmark evidence with visible `结论先说` / `核心对比` / `基准结论` / `下一步建议` / `附录` headings. If no object is specified, the skill auto-selects the highest-spend cost-active Campaign in the dominant objective bucket. Do not wait for the user to ask "where is the benchmark?"

**Creative / Ad benchmark:**

```text
Which creatives in this campaign are performing best vs. account baseline?
```

**Candidate discovery:**

```text
Find my highest-CVR ads and check whether they're actually strong vs. the account.
```

**Winners and draggers:**

```text
7514225548958957584 看热门 adg，也告诉我哪些拖后腿。
```

---

## Verification Checklist

1. `tt-ads` MCP is available and authenticated.
2. Skill lists accessible advertisers or accepts a provided `advertiser_id`.
3. Benchmark pool size is shown and non-zero.
4. Output states: objective used, grain, benchmark window, and sample count.
5. For account overview: visible `结论先说` / `核心对比` / `基准结论` / `下一步建议` / `附录` headings present; a WoW-only summary is incomplete.
6. Ask a follow-up ("is the CTR actually good?") — the skill reuses resolved context without re-pulling unless the target or window changed.
7. If artifacts are saved, confirm the conversation already contains the full conclusion before the `summary.md`, `result.json`, and `manifest.json` links.
8. For Chinese prompts, `summary.md` uses Chinese headings.
9. Every Winner and Dragger row includes a same-grain benchmark waterline ("better than N% of comparable Campaigns") — rows that only say "above account average" or "拖后腿" are incomplete.
10. Winners and Draggers are displayed one grain at a time; Campaign and Ad Group sections are separate.
11. Campaign and AdGroup object names are Markdown links when link fields are available; Ad / Creative object names are plain text by design. Object tables do not include a standalone ID column.
12. AdGroup links use the AdGroup identity inside `ad_ids`. Ad-grain output never links ordinary Creative or Smart+ / virtual Creative names, and must not use `creative_id`, `ad_material_id`, `creative_ids`, `virtual_creative_id`, or multiple `in_field_values` for one object-name link.
13. Status lookup is attempted before labeling any object as scalable; if unavailable, the skill says so explicitly.

If any step fails due to auth, permission, or empty report data, that is the real test result. Do not substitute local example data.

---

## Package Contents

```text
tt4b-account-benchmark/
├── SKILL.md                                    Skill instructions (runtime)
├── README.md                                   This file
├── evals/evals.json                            Evaluation test cases
├── scripts/
│   ├── compute-account-benchmark.mjs           Deterministic local benchmark computation (Node.js)
│   └── compute-account-benchmark.py            Deterministic local benchmark computation (Python fallback)
└── references/
    ├── account-benchmark-design.md             Benchmark math, eligibility, statistics
    ├── analysis-output.md                      Output format, caveat language, narrative structure
    ├── candidate-discovery.md                  Candidate ranking and evidence-tier logic
    ├── interactive-intake.md                   Cold-start UX and intake flow
    ├── mcp-report-contract.md                  MCP tool calls, report params, pagination
    ├── metric-catalog.md                       Metric names, API metric field names, aliases
    ├── objective-metric-profiles.md            Per-objective metric selection and language
    └── smart-plus-material-benchmark.md        Optional Smart+ material enrichment
```
