# Example 03 — Thin data / no fatigue (no fabrication)

## 3a — Not enough creative data
**User:** "Are my creatives fatiguing?"
**State:** all ads have baseline impressions < 1000 (new account, just launched).

**Expected behavior:**
- Apply the data floor: every ad is excluded as "insufficient data."
- Raise **`E103_NO_ADS`**: "Not enough creative data yet to judge fatigue — your ads need more
  delivery (≥ 1000 impressions over the baseline window) first." Stop. Do not fabricate fatigue.

## 3b — Healthy creatives, nothing fatiguing
**State:** every ad's recent CTR/CVR is at or above its baseline.
**Expected behavior:**
- Run the analysis, classify (mostly Scale / Watch), `spend_at_risk = 0`.
- Headline: **"No fatiguing creatives right now."** Still show analyzed/skipped counts + limits.
- Never invent a Retire item to look useful.

## 3c — Library scan returns nothing
**State:** `library_scan = yes` but `file_video_ad_search` / `file_image_ad_search` return no unused
assets (or error).
**Expected behavior:**
- Show "No unused library assets found." under the candidates section and **continue** — the plan is
  still delivered. The empty/failed library scan is NOT an error and must not block the output.
