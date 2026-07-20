# Recommendation Playbooks

Detailed recommendation menus for the four analysis passes in Step 3 of `SKILL.md`. Select the entries that match the campaign's objective, audience configuration, creative health signals, and vertical, then merge and rank per the SKILL.md instructions.

### Pass A: Objective-Based Recommendations

Route to the section matching the campaign's `objective_type` from MCP.

---

#### A1: Reach & Awareness / Video Views

**Signals to evaluate:**
- CPM above vertical benchmark → audience too narrow or bid too low
- Hook rate < 30% → creative is not stopping the scroll
- Frequency > 3 per user per week → audience saturation

**Recommendations to consider:**
- If CPM is above benchmark and audience is narrow: Broaden targeting — remove
  interest constraints and let TikTok's algorithm find the audience. Broad targeting
  (>80% country reach) achieves 15% lower CPA and 20% higher conversion rates on
  average vs. narrow segments.
- If hook rate < 25%: Brief creative team for new hook concept. For awareness, the
  hook is the unit — 90% of ad recall is formed in the first 6 seconds. Ads showing
  the product on screen drive a 65% increase in brand affinity and 25% uplift in recall.
- If frequency > 3: Rotate creative assets. Plan for new creative every 7–10 days.
  The sweet spot is 2–3× per week per user for efficient ad recall and awareness lift.
- If using Cost Cap on an awareness campaign: Switch to CPM/max delivery.
  Cost Cap limits reach on awareness objectives — this is a bidding strategy mismatch.
- If not using CBO across 3+ ad groups: Enable CBO to let budget flow to the ad
  groups with the best reach efficiency.
- If campaign flight is < 3 weeks: Awareness campaigns perform significantly better
  with duration. TikTok data shows 3–4 week campaigns drive 24.5% higher awareness
  than shorter campaigns; 5–6 weeks drives 5.7% higher brand association.
- If in-feed only with $50K+ budget: Surface the option of adding premium formats.
  TikTok Pulse adds an average +6.8% awareness lift (TikTok internal, Pulse product
  documentation). Note: "1.4× awareness / 3.0× purchase intent" figures found in some
  research pertain to campaigns using 10+ unique creatives vs. fewer than 5 — they
  measure creative diversity, not premium format bundling. Do not conflate these.

**Vertical-specific note for Awareness:**
- CPG/FMCG: Use 6-second view optimization to capture higher attention quality.
- Entertainment/Media: Lean into organic-style creative and trending audio.
  Entertainment verticals see hook rates 5–10 pts above average when audio matches
  trending content.
- Finance: Use educational hooks ("Did you know...") rather than product-first.
  Finance audiences are skeptical of ads that lead with the product.

---

#### A2: Traffic

**Signals to evaluate:**
- CTR below benchmark → ad is not compelling enough to drive clicks
- CPC rising → competition or declining relevance score
- Low hook rate → users not engaging before the CTA lands

**Recommendations to consider:**
- If CTR < vertical benchmark and hook rate > 25%: CTA may be weak or misaligned.
  Reinforce the CTA in the first 5 seconds, not just at the end. Test CTA variants.
- If CTR < vertical benchmark and hook rate < 25%: Hook is the problem, not the CTA.
  Prioritize new hook testing before CTA optimization.
- If optimization goal is CLICK (not LANDING_PAGE_VIEW): Switch to Landing Page View
  optimization — it filters out accidental taps and consistently delivers lower bounce rates.
- If landing page URL lacks UTM parameters: Add UTMs immediately — traffic quality
  is unmeasurable without cross-channel tagging.
- If audience is narrow (<1M estimated reach): Expand. Traffic campaigns need scale
  to let the algorithm find click-prone users within the pool.
- If pacing is low and budget is adequate: Check bid competitiveness. Traffic
  campaigns often underpace when CPC bid is below the market floor.

---

#### A3: App Install / App Event Optimization (AEO)

**Signals to evaluate:**
- High install volume but high CPI → audience or creative efficiency issue
- Low install volume → underbidding or underpacing; algorithm lacks signal
- AEO in use but < 50 installs/week → AEO is in learning phase, cannot optimize

**Recommendations to consider:**
- If CPI is above target and campaign < 14 days old: Do not adjust bids. The
  algorithm is in the learning phase — premature bid changes reset the learning cycle.
  Allow 7–14 days before evaluating CPI.
- If CPI is above target and campaign > 14 days old: Review creative. UGC showing
  real app usage in the first 3 seconds consistently outperforms polished product demos
  for app install objectives.
- If using AEO and weekly in-app events < 50: Move optimization goal upstream
  (e.g., Purchase → Add-to-Cart or Registration) until event volume is sufficient.
- If iOS and Android are in the same ad group: Separate them. iOS requires
  SKAdNetwork campaigns with different attribution logic. This always ranks as a
  🔴 immediate action.
- If budget per ad group < 50× CPI target: Increase to 50× CPI minimum. Below
  this floor, the algorithm cannot gather enough signal to exit the learning phase.
- If weekly in-app purchases exceed 100: Recommend enabling value-based optimization.
  VBO shifts spend toward the highest ROAS users and improves efficiency at scale.

---

#### A4: Web Conversion / Lead Generation

**Signals to evaluate:**
- CPA above target → signal weakness, bid strategy, or creative mismatch
- Low delivery despite adequate budget → Cost Cap may be constraining
- Conversion volume < 50/week → pixel signal insufficient for algorithm to optimize

**Recommendations to consider:**
- If CPA is above target and conversion volume < 50/week: Move the conversion event
  upstream (e.g., Add-to-Cart → View Content) until weekly event volume exceeds 50.
  The pixel needs data to find the right audience.
- If CPA is above target and conversion volume > 50/week: Review creative. Ads
  showing the product in the first 3 seconds drive 65% higher brand affinity. Ensure
  the value proposition is visible within 5 seconds.
- If Cost Cap is set but campaign < 14 days old: Switch to Lowest Cost / Maximum
  Delivery for the learning phase; re-engage Cost Cap after 50+ weekly conversions.
- If pixel is missing or not firing: 🔴 This is a launch-level blocker. Pause
  the campaign until the pixel is verified. A conversion campaign without pixel signal
  is optimizing blind.
- If audience is custom audiences only: Add a broader interest-based ad group to
  feed the funnel. Custom Audiences alone limit scale and prevent finding new high-intent users.
- If no conversion suppression audience: Add an exclusion list of recent converters
  (last 30–90 days depending on purchase cycle).
- If e-commerce with 50+ SKUs and no catalog/dynamic ads: Recommend Smart+ Catalog /
  Dynamic Product Ads — they personalize creative to user intent signals. Clinique's
  Smart+ Catalog Ads delivered 17% more cost-efficient purchases, 1.23× higher ROAS,
  and 27% CTR increase vs. manual (TikTok for Business case study, 2024 — single brand).
- If campaign has conversion history and is not on Smart+: Recommend Smart+ Web Campaigns.
  Smart+ Lead Gen example: Volvo case study (Feb 2025, TikTok for Business) showed 82%
  more leads and 75% lower CPL vs. manual campaign. Single brand — treat as indicative.
- For Smart+ Lead Gen: Set daily budget at 10× average daily CPA. Do not react to
  CPA spikes in the first 7 days. Add 2–5 new creatives rather than deleting underperformers
  during the learning phase.

---

### Pass B: Audience-Based Recommendations

Apply the following checks based on `audience_type` and targeting configuration.

| Audience Configuration | Signal | Recommendation |
|---|---|---|
| Broad / no targeting constraints | CTR < 0.5% | Problem is creative, not audience. Do not narrow targeting — brief creative team. |
| Interest-only targeting | Reach < 500K | Remove 1–2 interest constraints or enable Smart Targeting to auto-expand. |
| Custom Audience (retargeting) | Frequency > 4 per user | Retargeting pool is exhausted. Expand lookback window or add prospecting ad groups. |
| Lookalike only | No conversions after 7+ days | Lookalike source may be stale. Refresh the seed audience; add interest-based prospecting. |
| No Custom Audience exclusion | Conversion campaign | Add suppression list of recent converters (30–90 days). |
| Smart Targeting off | Any objective, underperforming | Enable Smart Targeting. Broad targeting achieves 15% lower CPA and 20% higher CVR vs. narrow. |

---

### Pass C: Creative Recommendations

Apply these checks based on ad-level data and creative performance metrics.

| Observation | Recommendation |
|---|---|
| Fewer than 3 creatives per ad group | 🔴 Add creatives. This is the most common cause of creative fatigue and delivery inefficiency. |
| No creative variants with different hooks | ⚠️ Test at minimum 3 hook variations for the same message — one usually outperforms the others by 2–3× on hook rate. |
| Spark Ads not in use + client has organic presence | 💡 Enable Spark Ads. They use organic posts as the ad unit, attributing all engagement to the organic post, compounding organic growth while paying for performance. |
| Smart Creative not enabled | 💡 Enable Smart Creative. It auto-generates format variants and identifies winners without additional creative production. |
| All creatives are produced/polished (no UGC) | 💡 Introduce UGC-style content. Mobile-shot UGC has a 63% chance of outperforming studio-shot creatives for purchases and installs (Demand Curve, 2023 — directional). Target an 80/20 or 70/30 UGC-to-polished ratio. |
| No voiceover in conversion creatives | 💡 VidMob analysis (1,400+ TikTok ads, 2020) found voiceover + written offer drove +87% conversion lift vs. no-audio. Speech-dense narration (≥4 words/second) showed +19% CVR lift. Directional — study predates Smart+. |
| Video length > 30 seconds | ⚠️ Completion rates drop sharply after 30 seconds. Edit to 15–20 seconds for performance objectives; 15–30 seconds max for awareness. |
| CTA absent or misaligned | ⚠️ CTA should appear within the first 5 seconds. 80% of top intent campaigns use a CTA prompt. Integrate naturally — creator says it, text overlay, or sticker. |
| Creative frequency ≥ 3.5 (last 7 days) | ⚠️ Begin rotating. Plan to replace high-frequency creatives within 7 days. |
| Creative frequency ≥ 5 (last 7 days) | 🔴 Rotate immediately. Sustained high frequency degrades engagement and increases CPM as relevance score declines. |
| Hook rate declining, VCR stable | Recut the first 3 seconds with a new hook — keep the body of the ad. |
| Hook rate AND VCR both declining | Full creative refresh needed, not just the hook. |

**Creative pipeline constraint:** Always factor in the user's stated creative pipeline
capacity. If the client can only produce 1–2 assets per week, recommend which single
creative to prioritize replacing — not a broad refresh.

---

### Pass D: Vertical-Specific Recommendations

Route to the section matching the vertical the user provided.

#### D1: CPG / FMCG

**Benchmark reference:**
| Metric | CPG Benchmark | Flag If |
|---|---|---|
| CTR | 0.6–0.9% | < 0.5% or > 1.5% |
| CPM | $7–$10 | > $12 |
| VCR (100%) | 28–35% | < 22% |
| Hook Rate (2s) | 30–38% | < 25% |
| Engagement Rate | 3–5% | < 2% |
| CPC | $0.60–$1.20 | > $1.50 |

**Vertical-specific tactics:**
- UGC and creator content consistently outperform brand-produced spots. If VCR or hook rate
  is below benchmark, audit whether creative looks native to the platform.
- 77% of TikTok users use the platform as part of their CPG shopping journey. "Discovery"
  creative (product in use) outperforms product-isolation ads.
- For CPG with TikTok Shop: Prioritize GMV Max campaign types for performance. TikTok/Nielsen
  CPG MMM meta-analysis (US, 16 NCSolutions studies, 2021–Q1 2024) found CPG advertisers
  could increase in-feed impression volume by 50% while maintaining efficient offline sales
  lift, with average ROAS of 2× the NCS median CPG benchmark. (Note: some secondary sources
  incorrectly cite "12×" — the primary source states 2×.)
- For campaigns at $50K+ spend: Recommend Brand Lift Studies to capture awareness and
  purchase intent lift that click-based metrics miss.

---

#### D2: Retail / E-commerce

**Benchmark reference:**
| Metric | Retail/E-comm Benchmark | Flag If |
|---|---|---|
| CTR | 0.8–1.2% | < 0.6% |
| CPM | $8–$14 | > $16 |
| VCR (100%) | 25–32% | < 20% |
| Hook Rate (2s) | 32–42% | < 25% |
| Engagement Rate | 3–6% | < 2% |
| CPC | $0.50–$1.00 | > $1.25 |

**Vertical-specific tactics:**
- For e-commerce with 50+ SKUs: Strongly recommend Smart+ Catalog / Dynamic Product Ads.
- Product-reveal creative (product in frame within first 2 seconds) drives above-benchmark
  hook rates in retail. If hook rate is below benchmark, check whether creative leads with
  a person/concept before the product.
- **GMV Max (critical for TikTok Shop brands):** As of 2025, GMV Max is the default
  campaign type for TikTok Shop Ads. Campaigns with 50+ eligible videos deliver 3–4×
  better results than those with <10. Target ROI of 3–5× with CPO of $8–$25. Use 1 GMV
  Max campaign per market; layer Search Ads on top for high-intent terms. Allow 5–7 days /
  ~40 conversions before judging performance.
- Maintain a minimum 10–12-creative library per campaign. Top-performing retail campaigns
  produce 20–50 creative variations per month. Minimum 12 videos/month is the TikTok-
  recommended floor to avoid ad fatigue at scale.

---

#### D3: Entertainment / Media

**Benchmark reference:**
| Metric | Entertainment Benchmark | Flag If |
|---|---|---|
| CTR | 0.7–1.1% | < 0.5% |
| CPM | $6–$10 | > $13 |
| VCR (100%) | 30–40% | < 22% |
| Hook Rate (2s) | 35–45% | < 28% |
| Engagement Rate | 5–9% | < 3% |
| CPC | $0.40–$0.90 | > $1.20 |

**Vertical-specific tactics:**
- If hook rate is below 35%, the ad is too "branded" — it needs to feel like organic
  entertainment content, not an ad.
- Use TikTok's Commercial Music Library and match to audio trending within Entertainment.
- For streaming/media launches: 15-second teaser creatives outperform longer trailers in paid;
  use the full trailer as organic content.
- Spark Ads outperform standard in-feed in Entertainment more than most verticals —
  authentic creator reactions to the property dramatically outperform paid production.
- Engagement rate is the leading performance indicator for Entertainment (not CTR or VCR).
  If engagement is below 5%, the content is not resonating culturally.

---

#### D4: Finance / Insurance

**Benchmark reference:**
| Metric | Finance Benchmark | Flag If |
|---|---|---|
| CTR | 0.4–0.7% | < 0.3% |
| CPM | $10–$18 | > $22 |
| VCR (100%) | 22–30% | < 18% |
| Hook Rate (2s) | 25–35% | < 20% |
| Engagement Rate | 2–4% | < 1.5% |
| CPC | $0.80–$2.00 | > $2.50 |

**Vertical-specific tactics:**
- Finance is the most expensive vertical on TikTok. Do not flag high CPM as a problem
  without comparing to the Finance benchmark — structurally higher CPMs are expected.
- Educational hooks ("Did you know..." / "Most people don't realize...") outperform
  product-first hooks. If hook rate is below benchmark, lead with an insight, not the product.
- Lead Gen campaigns should use TikTok's native Lead Gen forms rather than landing page
  redirects where possible — form completion rates are typically higher when users don't
  leave the platform.
- Review brand safety settings — recommend enabling TikTok's full GARM brand safety suite.
- Compliance flag: Finance creatives require legal review prior to flight. If the client's
  legal team has not reviewed the live ad copy, surface this as a ⚠️ regardless of
  performance status.

---

#### D5: App / Mobile Gaming

**Benchmark reference:**
| Metric | App/Gaming Benchmark | Flag If |
|---|---|---|
| CTR | 1.0–2.0% | < 0.8% |
| CPM | $6–$12 | > $15 |
| VCR (100%) | 25–35% | < 20% |
| Hook Rate (2s) | 35–45% | < 28% |
| Engagement Rate | 4–8% | < 3% |
| CPC | $0.30–$0.80 | > $1.00 |

**Vertical-specific tactics:**
- App/Gaming has the highest CTR benchmarks. If CTR is below 1.0%, this is almost always
  a creative problem, not an audience or bidding problem.
- Gameplay footage in the first 3 seconds is the top-performing hook format for Gaming.
  UGC "reaction" style creative consistently outperforms produced trailers.
- iOS and Android must be in separate ad groups — this is a structural requirement, not a
  preference. Flag any ad group targeting both.
- Value-Based Optimization is strongly recommended for gaming once weekly in-app purchases
  exceed 100.
- Playable ads drive significantly higher install rates for casual and hyper-casual games.

---

#### D6: Beauty / Personal Care

**Benchmark reference:**
| Metric | Beauty Benchmark | Flag If |
|---|---|---|
| CTR | 0.7–1.2% | < 0.5% |
| CPM | $7–$11 | > $14 |
| VCR (100%) | 28–38% | < 22% |
| Hook Rate (2s) | 32–42% | < 28% |
| Engagement Rate | 4–8% | < 3% |
| CPC | $0.50–$1.10 | > $1.40 |

**Vertical-specific tactics:**
- "Get ready with me" (GRWM), tutorial, and before/after formats consistently outperform
  polished brand spots.
- Up-close product texture and application footage is the highest hook-rate format in Beauty.
  If hook rate is below benchmark, check whether the first 2 seconds show the product in use.
- 92% of consumers trust peer recommendations over brand content. If all creatives are
  brand-produced, recommend introducing creator partnerships.
- TikTok Shop integration is a meaningful revenue driver for Beauty brands with a product catalogue.
- Sound design matters more in Beauty than most verticals (ASMR, product sounds, textures).
  Silent or background-music-only creatives underperform.

---

#### D7: Automotive

**Benchmark reference:**
| Metric | Automotive Benchmark | Flag If |
|---|---|---|
| CTR | 0.5–0.9% | < 0.35% |
| CPM | $9–$16 | > $20 |
| VCR (100%) | 22–32% | < 18% |
| Hook Rate (2s) | 28–38% | < 22% |
| Engagement Rate | 2–5% | < 1.5% |
| CPC | $0.70–$1.60 | > $2.00 |

**Vertical-specific tactics:**
- Automotive on TikTok skews toward discovery and top-of-funnel intent building. Set client
  expectations accordingly when evaluating conversion KPIs.
- TikTok's Automotive behavioral targeting (in-market signals, vehicle interest) is a strong
  differentiator. If using generic interest targeting, recommend switching.
- Creator content (real car owners, test drives) outperforms official brand footage for
  engagement rate.
- For dealership/local campaigns: Use geographic targeting at DMA or ZIP level. National
  targeting wastes budget on out-of-market users.
- Lead Gen forms outperform landing-page-redirect campaigns for test drive and quote requests.

---

#### D8: QSR / Food & Beverage

**Benchmark reference:**
| Metric | QSR/F&B Benchmark | Flag If |
|---|---|---|
| CTR | 0.6–1.0% | < 0.45% |
| CPM | $7–$11 | > $14 |
| VCR (100%) | 28–36% | < 22% |
| Hook Rate (2s) | 32–42% | < 26% |
| Engagement Rate | 4–7% | < 2.5% |
| CPC | $0.55–$1.10 | > $1.40 |

**Vertical-specific tactics:**
- Food content showing preparation, eating, or reaction consistently outperforms brand
  hero shots ("FoodTok" effect).
- For LTO campaigns: Lead with the offer, not the brand — "This is only here for 30 days"
  beats a logo reveal.
- Sound is disproportionately important for F&B (sizzling, crunching, pouring). Silent
  or music-only creatives underperform significantly.

---

#### D9: Travel / Hospitality

**Benchmark reference:**
| Metric | Travel Benchmark | Flag If |
|---|---|---|
| CTR | 0.55–0.95% | < 0.4% |
| CPM | $8–$14 | > $17 |
| VCR (100%) | 26–36% | < 20% |
| Hook Rate (2s) | 30–40% | < 24% |
| Engagement Rate | 3–6% | < 2% |

**Vertical-specific tactics:**
- Destination discovery content ("places you didn't know existed") and travel hack formats
  drive above-average hook rates.
- Remarketing is disproportionately valuable in Travel (consideration windows are long).
  Ensure Custom Audience retargeting covers 30, 60, and 90-day windows.
- Seasonal timing affects delivery efficiency — monitor CPM relative to seasonality.

---
