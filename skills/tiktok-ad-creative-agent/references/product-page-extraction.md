# Product Page Extraction

Use this reference when the user provides an Amazon listing, ecommerce page, app store page, landing page, PDF, document, screenshot, or uploaded product image.

## Extraction Goals

Capture enough verified facts to make strong ads without inventing product claims.

## Source Ledger Fields

- URL.
- Source type: URL, PDF, document, screenshot, uploaded image, or brand asset folder.
- Access date.
- Page title.
- Product name.
- Brand or seller.
- Product ID, ASIN, SKU, or handle when visible.
- Variant selected.
- Price and offer state if visible.
- Rating count and review count if visible.
- Bought-in-period or other social proof if visible.
- Product images saved or linked.
- Product reference image paths, URLs, page numbers, or screenshot regions.
- Feature bullets.
- Product description.
- Specs.
- Reviews or review themes, only when visible.
- Missing fields.
- Fields blocked by sign-in, region, dynamic loading, or anti-bot page.

## Amazon-Specific Notes

- Preserve the ASIN and selected variant.
- Treat price and availability as volatile. Include the extraction date.
- Do not use review text unless it is visible and labeled as customer review content.
- Do not turn one review into a general market claim.
- Do not invent endorsements, awards, badges, or ranking.
- If the Buy Box is unavailable or regional pricing is unclear, avoid offer-led creative unless the user confirms an offer.

## Ad-Relevant Extraction

Prioritize:

- First-screen promise.
- Feature bullets.
- Product photos and lifestyle photos.
- Product reference images suitable for image/video generation or post-production compositing.
- Specs that create a visual proof moment.
- Objections implied by reviews or Q&A.
- Competitive differentiators.
- Any limitation that should not be hidden.

## Output Shape

Return:

- Product facts.
- Proof inventory.
- Visual asset inventory.
- Product reference image inventory and any quality risks.
- Offer state.
- Audience hypothesis.
- Claim boundaries.
- Missing information.
- Recommended confirmation questions.
