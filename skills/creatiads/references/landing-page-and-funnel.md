# Landing Page And Funnel

Use this reference for landing page performance, product/SKU grouping, app discovery, W2A routing, redirect quality, and click-to-conversion diagnosis.

## Evidence Chain

1. Pull candidate pools first: up to 3000 ad-level rows and up to 3000 Smart+ ad-level rows by spend when the MCP
   report route supports pagination.
2. Detect upgraded Smart+ asset granularity at the report layer before enrichment:
   - `dimensions=["ad_id"]` with `campaign_automation_type=UPGRADED_SMART_PLUS_CREATIVE` means `ad_id` is a
     creative identity.
   - `dimensions=["ad_id_v2"]` with `campaign_automation_type=UPGRADED_SMART_PLUS` and non-empty `ad_id_v2` means
     `ad_id_v2` is the Smart+ asset/ad configuration identity.
3. Select the final HTML ad/creative rows from those pools.
4. Prefer report-level destination fields when available.
5. For regular ads, enrich only the selected rows with ad detail and ad group detail.
6. For upgraded Smart+ landing and asset grouping, use the `ad_id_v2` path first: de-duplicate `ad_id_v2`, call
   Smart+ ad detail in batches of at most 50, extract `landing_page_url_list[0].landing_page_url`, and backfill that
   URL to the creative/spend rows under the same `ad_id_v2`.
7. For Smart+ campaigns and upgraded Smart+ ads, enrich only the selected rows with the corresponding Smart+ detail
   route and Smart+ material report routes when needed.
8. Preserve both regular report identity and Smart+ identity when both exist.
9. Extract URL evidence by kind: `landing`, `app_store`, `deeplink`, `product`, `catalog`, `shop`, `creative_asset`, and `unknown`.
10. Canonicalize landing URLs by scheme, host, path, product/SKU keys, and campaign-safe query parameters.
11. Aggregate spend, clicks, result/conversion, value, cost, and ROAS by normalized URL/SKU/app path for the selected
   rows and their parent entities.
12. Keep media/CDN URLs out of landing-page grouping; use them only as creative evidence.

## Destination Fallback

For upgraded Smart+ rows, use:

1. `ad_url` from the `ad_id_v2` report row.
2. `landing_page_url_list[0].landing_page_url` from Smart+ ad detail.
3. Smart+ configuration, deeplink, page, app, catalog, shop, or promoted-object fields.
4. Parent ad group fallback.
5. Campaign or legacy Smart+ fallback only when the row is legacy Smart+, not as the upgraded Smart+ primary path.

For non-upgraded rows, use:

1. `ad_url` from the `ad_id` report row.
2. Regular ad detail by final `ad_id`.
3. Ad group destination/download URL or ad group detail.
4. Legacy Smart+ campaign detail only when applicable.

## W2A Classification

Classify as W2A/app when evidence includes:

- Adjust, Appsflyer, OneLink, Branch, or similar deferred deep-link domains.
- Self-owned landing domains that ultimately redirect to App Store or Google Play.
- App ID, app name, app download URL, app event, or promoted app field.

Do not recommend web purchase-only optimization for W2A unless web purchase events are active and decision-grade.

## Funnel Proxies

| Stage | Evidence |
| --- | --- |
| Impression to attention | video views, engaged view, reach/frequency |
| Attention to click | CTR and clicks |
| Click to destination | landing URL, app store URL, deeplink, destination visit |
| Destination to conversion | install, registration, trial, subscribe, purchase, lead, or custom event |
| Web commerce | product view, add to cart, checkout, purchase, value |

## Diagnostics

| Symptom | Likely issue | Action |
| --- | --- | --- |
| High CTR and weak result | page, offer, redirect, or store mismatch | inspect destination and event quality |
| Good store click and weak install | store listing, geo, device, or promoted app mismatch | inspect app and audience |
| High install and weak registration/trial | onboarding or low-intent traffic | optimize deeper event |
| Add to cart but no purchase | checkout, price, shipping, or trust friction | inspect offer and checkout |
| URL unresolved for high spend | incomplete object enrichment | mark `partial` and run deeper enrichment |

## Output

Return:

- landing/app/store destinations found
- URL/SKU/app ranking by spend, clicks, result, value, cost, and ROAS when active
- unresolved object list with spend share
- W2A classification and metric preset implication
- broken, mismatched, or suspicious redirect notes
