# Vertical Report Templates

Use this reference for user-type-specific HTML reports. Markdown outlines here are templates; formal output should be `report.html` plus run-directory artifacts.

## Universal Header

Every vertical report begins with:

```text
Scope: platform, account or advertiser IDs, date range, comparison range
User type: resolved type, confidence, and evidence source
Metric set: preset name plus active and unavailable metrics
Coverage: full | batch | partial | sampled | failed_with_reason
Limits: platform-reported data only unless first-party data was provided
```

Every report must explicitly show impressions, clicks, spend, conversion/result, and revenue/value. If revenue/value is missing, keep it visible and mark it `supported_empty`, `unsupported`, `not_queried`, or `partial` according to the probe evidence.

## Ecommerce Report

Sections:

1. Platform KPI: spend, impressions, clicks, CTR, CPC, CPM, conversion, cost.
2. Purchase/value proxy: purchase, value, ROAS, payment, catalog/shop metrics when active.
3. Funnel proxy: product detail view, view content, add to cart, checkout, purchase.
4. Landing/product URL concentration and SKU grouping when available.
5. Creative and placement drivers.
6. Actions: scale, fix offer/landing, refresh creative, reduce waste.

## Utility Or W2A Report

Sections:

1. W2A/app evidence: tracker domain, store destination, app metadata, app event health.
2. Traffic path: impression to click to destination to install/registration/trial/subscribe.
3. App outcomes and value metrics when active.
4. SKAN/SAN availability and delay risk.
5. Creative hook and audience quality.
6. Actions: optimize deeper event, fix redirect/store mismatch, separate web and app diagnostics.

## Short Drama Report

Sections:

1. Core metric coverage with probe supplement status.
2. Video hook and retention: 2s, 6s, quartiles, completion, engaged-view.
3. Creative retention ranking: top retention, top conversion, high-spend low-retention, cheap-click low-retention, refresh candidates.
4. Click/store/app path evidence.
5. Install/register/subscribe/purchase proxy.
6. Episode or offer angle diagnosis.
7. Actions: opening refresh, audience split, deeper event optimization.

## Casual Game Report

Sections:

1. CPI/result efficiency.
2. Tutorial, retention, in-app ad, and purchase proxies when active.
3. Creative hook and gameplay clarity.
4. Geo/device/placement quality.
5. Actions: avoid cheap install traps; optimize toward quality events.

## Midcore Or Hardcore Game Report

Sections:

1. Install and registration baseline.
2. Role creation, level, achievement, retention, purchase proxy.
3. Creative/audience fit by genre promise.
4. Actions: prioritize downstream quality over CPI.

## Financial Leads Report

Sections:

1. Lead/application baseline.
2. Apply to credit to disbursement proxy when active.
3. Geo/device/placement and compliance-safe traffic quality.
4. Actions: reduce cheap unqualified leads; optimize toward deeper qualified event.

## Novel Report

Sections:

1. Video/story hook.
2. Install/register/trial/subscribe/purchase proxy.
3. Creative premise and audience resonance.
4. Actions: improve hook and optimize toward subscription or purchase when available.

## Entertainment Report

Sections:

1. Attention and engagement.
2. Install/register/login/subscribe/purchase proxy.
3. Live, messaging, placement, and creative resonance.
4. Actions: separate cheap engagement from meaningful activation.

## Search Arbitrage Report

Sections:

1. CTR, CPC, CPM, outbound or destination click proxy.
2. Device/placement/geography cost mix.
3. Conversion/value proxy when active.
4. Actions: isolate low-quality cheap clicks; maintain margin discipline only when external margin is provided.

## Social Report

Sections:

1. Install/register/login baseline.
2. Subscribe/purchase/custom-event proxy when active.
3. Audience quality and creative social proof.
4. Actions: optimize toward activation, not only install.

## Agency Or Mixed Report

Sections:

1. Per-account user-type table.
2. Core cross-account health: spend, clicks, result, cost.
3. Vertical-specific findings by comparable account group.
4. Coverage, sampling, and fallback notes.

Do not compare all accounts by one vertical-specific metric when user types differ.
