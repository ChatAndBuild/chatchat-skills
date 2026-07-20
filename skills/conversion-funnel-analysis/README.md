\# TikTok Conversion Funnel Analyst



\*\*Sophisticated funnel optimization agent that maps multi-stage conversion funnels, identifies drop-off points, diagnoses root causes, and forecasts the impact of proposed optimizations.\*\*



\---



\## Quick Start



\### Installation

1\. Add this Skill to your StationOne workspace (or other AI tools directly - like Claude, ChatGPT, or Gemini)

2\. Ensure the \*\*TikTok for Business Connector\*\* is enabled and authenticated

3\. Verify TikTok Pixel is installed and tracking conversion events

4\. Activate the "TikTok Conversion Funnel Analyst" skill



\### Basic Usage

```

"Analyze the conversion funnel for campaign 33445566 over the last 

30 days. I want to know where people are dropping off and why."

```



The Skill will:

\- Map your complete conversion funnel (impressions → purchase)

\- Calculate drop-off rates at each stage

\- Identify critical leak points

\- Diagnose root causes and provide optimization recommendations



\---



\## Target Platform



\*\*Compatible with:\*\*

\- ✅ StationOne (primary platform)

\- ✅ Claude (Anthropic)

\- ✅ ChatGPT (OpenAI)

\- ✅ Gemini (Google)



\*\*Platform-specific notes:\*\*

\- Pixel event tracking required for detailed funnel analysis

\- Segment breakdowns and cross-reference possible via StationOne with visual charts and MMP Data (Appsflyer, Adjust, Singular).



\---



\## Prerequisites / Dependencies



\### Required

\- \*\*TikTok for Business MCP Connector\*\* (authenticated)

\- \*\*TikTok Pixel installed\*\* on website/app with event tracking enabled

\- Valid TikTok Ads account with Advertiser ID

\- API access with the following permissions:

&#x20; - `campaign.read`

&#x20; - `adgroup.read`

&#x20; - `reporting.read`

&#x20; - `pixel.read` (for event data)



\### Conversion Events Setup

Minimum required pixel events:

\- ✅ `ViewContent` (page view)

\- ✅ `AddToCart` or `InitiateCheckout`

\- ✅ `CompletePayment` or custom conversion event



Optional but recommended:

\- `ClickButton`

\- `Search`

\- `AddPaymentInfo`



\### Runtime Environment

\- No local dependencies

\- Cloud-based execution via StationOne or compatible AI platform

\- Minimum data requirement: 1,000 clicks or 14 days of data for statistical validity



\### Additional MCPs

\- \*\*None required\*\* - operates exclusively with TikTok for Business MCP

\- Optional: Google Analytics MCP for cross-platform funnel comparison (not required)



\---



\## Configuration



\### Default Settings

```yaml

funnel\_stages: auto\_detect               # Options: auto\_detect | custom

date\_range: 30                           # Days of historical data to analyze

minimum\_sample\_size: 1000                # Minimum clicks for analysis

leak\_threshold\_critical: 0.80            # >80% drop = critical leak

leak\_threshold\_moderate: 0.50            # 50-80% drop = moderate leak

segmentation\_enabled: true               # Break down by device, placement, etc.

include\_video\_engagement: true           # Analyze video funnel separately

benchmark\_source: industry\_standard      # Options: industry\_standard | account\_average

```



\### Configurable Parameters



| Parameter | Description | Default | Valid Range |

|-----------|-------------|---------|-------------|

| `funnel\_type` | Funnel model to use | standard\_ecommerce | standard\_ecommerce, lead\_gen, app\_install, custom |

| `attribution\_window` | Click-to-conversion window | 7\_days | 1\_day, 7\_days, 28\_days |

| `segmentation\_dimensions` | How to break down funnel | device, placement | device, placement, audience, creative, geo |

| `video\_completion\_thresholds` | Video engagement milestones | 2s, 6s, 100% | Comma-separated values |

| `forecast\_confidence\_interval` | Projection accuracy level | 90% | 80%, 90%, 95% |



\### Custom Funnel Definition

```yaml

custom\_funnel:

&#x20; stage\_1: impressions

&#x20; stage\_2: clicks

&#x20; stage\_3: page\_view           # Pixel event: ViewContent

&#x20; stage\_4: add\_to\_cart         # Pixel event: AddToCart

&#x20; stage\_5: initiate\_checkout   # Pixel event: InitiateCheckout

&#x20; stage\_6: purchase            # Pixel event: CompletePayment

```



\### Environment Variables

```

TIKTOK\_ADVERTISER\_ID=<your\_advertiser\_id>

TIKTOK\_PIXEL\_ID=<your\_pixel\_id>

FUNNEL\_TYPE=standard\_ecommerce

MIN\_SAMPLE\_SIZE=1000

```



\---



\## Common Errors and Troubleshooting



\### Error: "Pixel event data unavailable"

\*\*Cause:\*\* TikTok Pixel not installed or no events tracked in date range  

\*\*Solution:\*\*

\- Verify pixel installation: https://ads.tiktok.com/i18n/events\_manager

\- Ensure pixel is firing on all key pages (test via TikTok Pixel Helper)

\- Check if events are passing correctly (look for "Test Events" in Events Manager)

\- Reduce `date\_range` to include period with known traffic



\### Warning: "Insufficient sample size for segment analysis"

\*\*Cause:\*\* <1,000 clicks in one or more segments (e.g., mobile, desktop)  

\*\*Solution:\*\*

\- Increase `date\_range` to 60 or 90 days

\- Disable segmentation or reduce segmentation dimensions

\- This warning is informational; analysis proceeds with available data



\### Error: "Video engagement data not found"

\*\*Cause:\*\* Campaign uses image ads or video tracking not enabled  

\*\*Solution:\*\*

\- Disable `include\_video\_engagement` for image-only campaigns

\- For video campaigns, ensure video metrics are tracked in TikTok reporting

\- Check if campaign uses Video Ads (not Spark Ads from creator accounts)



\### Issue: "Funnel shows >100% progression at a stage"

\*\*Cause:\*\* Users entering funnel mid-stage (e.g., direct traffic to cart page)  

\*\*Explanation:\*\*

\- This is normal for e-commerce sites with multiple traffic sources

\- Indicates non-TikTok traffic (direct, organic, email) also converting

\- Funnel shows TikTok-attributed conversions may exceed TikTok clicks



\*\*Solution:\*\*

\- Use `attribution\_window=1\_day` for stricter attribution

\- Filter to view-through vs click-through attribution separately

\- Accept this as informational (total conversions > TikTok-attributed)



\### Error: "Benchmark data unavailable for selected industry"

\*\*Cause:\*\* Industry-specific benchmarks not loaded or invalid industry type  

\*\*Solution:\*\*

\- Switch to `account\_average` benchmark

\- Manually specify custom benchmark thresholds

\- Use absolute performance (no benchmarking)



\---



\## Limitations and Caveats



\### Known Limitations

1\. \*\*Cross-Device Tracking\*\*: Cannot track users who click on mobile but convert on desktop (unless logged in)

2\. \*\*Ad Blockers\*\*: Users with ad blockers may not fire pixel events (5-15% underreporting)

3\. \*\*iOS 14.5+ ATT\*\*: Limited tracking for iOS users who opt out of tracking

4\. \*\*Attribution Windows\*\*: 7-day default; longer customer journeys may be incomplete



\### Edge Cases

\- \*\*Multi-Touch Attribution\*\*: Funnel shows last-click attribution only (no multi-touch credit)

\- \*\*Return Customers\*\*: Funnel includes both new and returning customers (no segmentation)

\- \*\*Cart Abandonment Retargeting\*\*: Users retargeted may show up twice in funnel

\- \*\*Coupon/Promo Impact\*\*: Discount codes may artificially improve checkout conversion



\### Industry Benchmarks (for reference)



| Funnel Stage | E-Commerce | Lead Gen | App Install |

|--------------|------------|----------|-------------|

| Click-Through Rate | 1-3% | 2-5% | 1-2% |

| Landing → Engagement | 60-80% | 70-90% | 80-95% |

| Engagement → Conversion | 10-30% | 15-40% | 5-15% |

| Overall Conversion Rate | 0.5-2% | 2-8% | 0.2-1% |



\### Best Practices

\- ✅ Analyze funnels monthly or after major changes

\- ✅ Use 30-day windows for stable insights (14 days minimum)

\- ✅ Segment by device first (mobile vs desktop shows biggest variance)

\- ✅ Cross-reference with Campaign Health Auditor

\- ⚠️ Don't optimize on single-day anomalies

\- ⚠️ Consider external factors (sales, seasonality, competitor activity)

\- ⚠️ A/B test landing page changes before full rollout



\---



\## Contact Information



\### Maintainer

\*\*StationOne Product Team\*\*  

Email: support@stationone.ai  

\-----

\*\*Version:\*\* 1.0.1

\*\*Last Updated:\*\* June 2026  

\*\*License:\*\* Proprietary  

\*\*Skill Package:\*\* `conversion-funnel-analysis-v1.0.0.zip`

