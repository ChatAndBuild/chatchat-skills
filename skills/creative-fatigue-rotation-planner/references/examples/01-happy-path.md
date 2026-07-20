# Example 01 — Happy path (clear fatigue, real spend-at-risk)

**User:** "Which of my creatives are getting tired and what should I rotate?"

**Account state:** advertiser `7449196078391672848` (KEYSHU VIỆT NAM, **VND**), recent 3d vs baseline
30d. `account_avg_cpa ≈ ₫2,325`. Ads:
- "Hook v2 - Dance" — conversion ad (baseline conversion 800): recent CTR 0.31% / base 0.72%; recent CVR 1.1% / base 2.0%; recent spend ₫4,000,000; baseline impr 50,000.
- "Keyshu Việt Nam" — real ad (baseline conversion 11,966): recent CTR ~2.5% ≥ base 2.43%; CPA ≤ avg; baseline impr 2,874,445.
- "Consideration clip" — awareness ad (baseline conversion 0): recent CTR 0.95% / base 1.0%; baseline impr 50,000.
- "New Clip" — baseline impr 600.

**Expected behavior:**
1. Stage 0 resolves the advertiser (pasted id); `advertiser_info_get` → currency VND.
2. Stage 2: recent report (sync `report_integrated_get`), baseline report (async
   `report_task_create`→`report_task_check`→`report_task_download`), ad↔creative names via
   `smart_plus_ad_get`/`ad_get`, optional library via `file_video_ad_search`/`file_image_ad_search`.
   Metric is **`conversion`** / **`conversion_rate`**.
3. Classify:
   - "Hook v2 - Dance" → **RETIRE** (conversion ad; CTR ratio 0.43<0.6 AND CVR ratio 0.55<0.7), ₫4.0M at risk.
   - "Keyshu Việt Nam" → **SCALE** (recent CTR ≥ baseline, CPA below average).
   - "Consideration clip" → awareness, CTR-only, ratio 0.95 → **Watch/none** (must NOT Retire on a missing CVR).
   - "New Clip" → **excluded** (thin data, < 1000 impressions).
4. Headline: **spend at risk = ₫4,000,000**.
5. Plan rendered, Retire sorted by recent spend (★ on biggest), Retire → `manage-creative`, Scale → `optimize-budget`.
6. **No write tool is ever called.**

Grader checks: conversion ad judged on CTR+CVR; awareness ad judged on CTR only (not Retire on a
missing CVR); thin-data ad excluded; spend-at-risk = sum of Retire recent spend.
