# Fatigue criteria — creative-fatigue-rotation-planner (scoring contract)

Deterministic rules. `SKILL.md` summarizes; this file is the **full contract** the report and the
eval grader score against. Verified against the live TikTok MCP (`report_integrated_get`, ad level).

## Inputs (per ad, two NON-overlapping windows)
From `report_integrated_get` (`data.list[].metrics`, returned as **strings** — parse to numbers):
a **recent** window (default last 3 days) and a **non-overlapping prior baseline** (default the 30
days ending the day *before* the recent window starts):
`spend, impressions, clicks, ctr, conversion, conversion_rate (CVR), cpm, video_play_actions, ad_name`.
`cpm` and `video_play_actions` are **required, not optional** — for video-views / reach ads (a large
share of real accounts) they are the *only* valid engagement metric; pulling without them leaves those
ads unjudgeable. Verified live: `7415418166391832593` (₫806M, ~all video-views), `7595534274158903297`,
`7631551715865657362`.

> ⚠️ **Windows must not overlap.** If the baseline includes the recent window, a recent decline is
> compared against itself and the signal is diluted. Verified live: on an active account, an
> overlapping 30-day baseline hid real week-over-week movement. Baseline = the period *before* recent.

> The conversion metric is **`conversion`** (singular) and the rate is **`conversion_rate`**.
> Money is in the advertiser's currency (no decimals for VND).

## Account baseline (for the Scale rule)
`account_avg_cpa = Σ spend / Σ conversion` over analyzed ads (`n/a` if no conversions).

## Engagement metric by objective (decides which signal applies)
Treat an ad as a **conversion ad** if its `baseline conversion > 0` (or its campaign objective is a
conversion type) → judge on **CVR / CPA**. Otherwise pick the awareness engagement metric by objective:
`TRAFFIC` / `BRAND_CONSIDERATION` / `ENGAGEMENT` → **CTR**; `VIDEO_VIEWS` → **cost-per-view**
(`spend / video_play_actions`) or view-rate; `REACH` → **CPM**. **Never judge a VIDEO_VIEWS / REACH ad on
CTR** — they optimize for views/reach and have ~0 clicks by design (verified live: NUXE / vivo / CP Foods
video-view ads). Never flag an awareness ad for a CVR it lacks.

**Pick the metric per ad, not per account.** One advertiser commonly mixes objectives in the same window —
traffic + video-views + live-conversion ads side by side (verified live: `7119328366494220289` ₫257M and
`7591834723639656465` run video-views *and* click/conversion ads at once). If the campaign objective wasn't
fetched, infer per ad from the metric signature: `conversion > 0` → conversion ad (CVR/CPA);
`video_play_actions ≫ clicks` with `ctr ≈ 0` → video-views/reach (cost-per-view / CPM); `video_play_actions = 0`
with real clicks → click objective (CTR / CPC). Then rank each ad only against **same-objective** peers.
**Anchor the inference on the campaign** (group by `campaign_name`): same-campaign ads share one objective, so
a **near-zero-CTR ad sitting in a click/consideration campaign** (whose other ads earn real CTR) is a
**bottom-CTR Retire candidate, not a "cheap view"** — only call an ad video-views/reach when its whole
campaign optimizes for views/reach. Verified live: Keyshu `Consideration Ads_2026` (`1858268013645842`,
BRAND_CONSIDERATION) spans ad CTR 0.05%→4.10% — judge them all on CTR; the 0.05% ad is a Retire.

## Data floor — exclude FIRST, never flag
- **F1 thin data:** `baseline impressions < 1000` → "insufficient data," excluded, counted as skipped.
- **F2 tiny spend:** `recent_spend < spend floor` (e.g. `< ₫500,000` / `$20` over the recent window —
  state it) → may be **Watch** but never **Retire** (not enough money at risk to act).
- **F3 paywalled:** a metric is `n/a` → that signal unavailable; if CTR itself is unavailable, skip
  the ad with a note. **Never guess.**

## Signal A — time-decay (preferred, precise; needs the ad in BOTH windows)
- **Engagement-metric fatigue:** the ad's engagement metric (per above) worsened ≥ 40% vs baseline —
  CTR or view-rate ↓ ≥ 40%, or cost-per-view / CPM ↑ ≥ 40% (for click-objectives = `recent_ctr < baseline_ctr × 0.6`).
- **CVR fatigue (conversion ads only):** `recent_cvr < baseline_cvr × 0.7`  (≥ 30% drop).

## Signal B — vs current peers (always available; handles creative churn)
Most advertisers rotate creatives fast (flash-sale bursts), so few ads persist across windows and
Signal A finds little. For each CURRENT ad (`recent impressions ≥ 1000`), rank it vs the account's
**current same-objective ads**: `recent_ctr` (awareness) plus `recent_cvr` / recent CPA (conversion).
**Bottom-third** vs peers (with meaningful spend) → a Retire candidate; **top-third** → a Scale
candidate. Special case: a **conversion ad with meaningful spend + clicks but `conversion = 0`**
(clicks that don't convert) is ALWAYS a Retire, regardless of age. Report **coverage/mode**: how many
ads have cross-window history (A) vs are fresh (B only).

## Classification — each ad gets EXACTLY ONE bucket
| Bucket | Rule | Severity |
|---|---|---|
| **Retire** | time-decay fatigue (A) OR conversion ad with spend+clicks but `conversion=0` OR bottom-third vs current same-objective peers (B); AND `recent_spend ≥ spend floor` | 🔴 |
| **Scale** | top-third vs current peers (high CTR; conversion: high CVR / low CPA) and not decaying | 🟢 |
| **Watch** | mild decline (`0.6 ≤ recent_ctr / baseline_ctr < 0.8`), mid-pack, or thin data | 🟡 |

## Headline — spend at risk
```
spend_at_risk = Σ recent_spend over RETIRE ads
```
If there are zero Retire ads → **"No fatiguing creatives right now."** Never invent fatigue.

## Worked example (auditable)
- **"Hook v2 - Dance"** (conversion ad, baseline conversion > 0): recent CTR 0.31% / baseline 0.72%
  → `0.43 < 0.6` ✓ CTR fatigue; recent CVR 1.1% / baseline 2.0% → `0.55 < 0.7` ✓ CVR fatigue; recent
  spend ₫4.0M ≥ floor → **RETIRE**.
- **"Keyshu Việt Nam"** (real ad, baseline CTR 2.43%, conversion 11,966): if recent CTR holds ≥
  baseline and CPA ≤ average → **SCALE**.
- **Awareness ad, 0 conversions, recent CTR 0.95% / baseline 1.0%** → ratio 0.95, CVR not applied →
  **Watch/none** (not Retire on a missing CVR).
- **"New Clip"**: baseline impressions 600 `< 1000` → **excluded** (thin data, skipped).
