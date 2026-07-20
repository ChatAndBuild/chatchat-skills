\# TikTok Campaign Health Auditor



\*\*Comprehensive diagnostic agent that conducts multi-layered health checks across campaigns, identifying issues, opportunities, and providing prioritized recommendations with quantified health scores.\*\*



\---



\## Quick Start



\### Installation

1\. Add this Skill to your StationOne workspace or other related AI toolset from OpenAI, Anthropic or Google

2\. Ensure the \*\*TikTok for Business Connector\*\* is enabled and authenticated

3\. Activate the "TikTok Campaign Health Auditor" skill



\### Basic Usage

```

"Run a full health check on campaign 11223344. I'm presenting to the 

client tomorrow and need to know what's working and what needs fixing."

```



The Skill will:

\- Analyze campaign structure, delivery, and performance

\- Generate a health score (0-100)

\- Identify critical issues, warnings, and opportunities

\- Provide prioritized action items



\---



\## Target Platform



\*\*Compatible with:\*\*

\- ✅ StationOne (primary platform)

\- ✅ Claude (Anthropic)

\- ✅ ChatGPT (OpenAI)

\- ✅ Gemini (Google)



\*\*Platform-specific notes:\*\*

\- Full diagnostic features available only on StationOne

\- Creative fatigue analysis requires TikTok Connector integration

\- Limited visual reporting on non-StationOne platforms



\---



\## Prerequisites / Dependencies



\### Required

\- \*\*TikTok for Business MCP Connector\*\* (authenticated)

\- Valid TikTok Ads account with Advertiser ID

\- API access with the following permissions:

&#x20; - `campaign.read`

&#x20; - `adgroup.read`

&#x20; - `ad.read`

&#x20; - `reporting.read`

&#x20; - `creative.read`

&#x20; - `tool.read` (for diagnostic insights)



\### Runtime Environment

\- No local dependencies

\- Cloud-based execution via StationOne or compatible AI platform

\- Minimum data requirement: 7 days of campaign activity for comprehensive audit



\### Additional MCPs

\- \*\*None required\*\* - operates exclusively with TikTok for Business MCP

\- Optional: Google Analytics MCP for landing page analysis (not required)



\---



\## Configuration



\### Default Settings

```yaml

audit\_depth: comprehensive               # Options: quick | standard | comprehensive

date\_range: 30                           # Days of historical data to analyze

health\_score\_weighting:

&#x20; delivery\_status: 0.30                  # 30% weight

&#x20; performance\_metrics: 0.40              # 40% weight

&#x20; creative\_health: 0.20                  # 20% weight

&#x20; account\_structure: 0.10                # 10% weight

benchmark\_comparison: account\_average    # Options: account\_average | industry\_standard

include\_recommendations: true

prioritize\_by: impact                    # Options: impact | effort | impact\_effort\_ratio

```



\### Configurable Parameters



| Parameter | Description | Default | Valid Range |

|-----------|-------------|---------|-------------|

| `audit\_scope` | What to analyze | all | all, delivery, performance, creative, structure |

| `benchmark\_source` | Comparison baseline | account\_average | account\_average, industry, custom |

| `creative\_fatigue\_threshold` | Frequency trigger for fatigue | 5.0 | 3.0 - 10.0 |

| `min\_performance\_period` | Days of data required | 7 | 3 - 90 |

| `health\_score\_threshold\_good` | Score >= this is "healthy" | 75 | 50 - 100 |

| `health\_score\_threshold\_poor` | Score < this is "critical" | 50 | 0 - 75 |



\### Environment Variables

```

TIKTOK\_ADVERTISER\_ID=<your\_advertiser\_id>

AUDIT\_DEPTH=comprehensive

BENCHMARK\_SOURCE=account\_average

OUTPUT\_FORMAT=detailed\_report

```



\---



\## Common Errors and Troubleshooting



\### Error: "Creative fatigue analysis failed"

\*\*Cause:\*\* Missing `creative.read` permission or no active creatives  

\*\*Solution:\*\*

\- Verify API permissions include creative access

\- Ensure campaign has at least 1 active ad creative

\- Check if creative assets were recently deleted



\### Warning: "Health score may be inaccurate - limited data"

\*\*Cause:\*\* Campaign has <7 days of data or <500 impressions  

\*\*Solution:\*\*

\- This is informational; health score still calculated but with lower confidence

\- Wait for more data before making major decisions

\- Use "quick" audit mode for new campaigns



\### Error: "Unable to retrieve diagnostic insights"

\*\*Cause:\*\* TikTok's `tool\_diagnosis\_get` API temporarily unavailable  

\*\*Solution:\*\*

\- Retry audit in 15-30 minutes

\- Health check will complete without TikTok's native suggestions

\- Manual diagnostic recommendations still provided



\### Issue: "Health score changed drastically between audits"

\*\*Cause:\*\* Recent performance shift or campaign modifications  

\*\*Solution:\*\*

\- This is expected behavior; health scores reflect real-time status

\- Review "Change Log" in audit report for what changed

\- Compare 7-day vs 30-day performance to identify trends



\### Error: "Benchmark data unavailable"

\*\*Cause:\*\* No historical account data or invalid industry selection  

\*\*Solution:\*\*

\- Switch to `account\_average` benchmark

\- Ensure account has 30+ days of historical data

\- For new accounts, use absolute thresholds instead of benchmarks



\---



\## Limitations and Caveats



\### Known Limitations

1\. \*\*Real-Time Lag\*\*: Audit reflects data from last sync (\~15-60 min delay from Ads Manager)

2\. \*\*Cross-Campaign Dependencies\*\*: Cannot detect budget competition between campaigns

3\. \*\*External Factors\*\*: Health score doesn't account for market changes, competitors, or seasonality

4\. \*\*Smart+ Limited Visibility\*\*: Reduced diagnostic depth for Smart+ campaigns (black-box optimization)



\### Edge Cases

\- \*\*Recently Modified Campaigns\*\*: Changes made <24 hours ago may not be reflected in health score

\- \*\*Paused Campaigns\*\*: Health audits still run but recommendations may be irrelevant

\- \*\*Multi-Country Campaigns\*\*: Creative fatigue calculated globally (not per-country)

\- \*\*A/B Tests\*\*: Experimental ad groups may show "poor" health during testing phase



\### Health Score Interpretation



| Score Range | Status | Typical Action |

|-------------|--------|----------------|

| 90-100 | Excellent | Maintain and scale |

| 75-89 | Good | Minor optimizations |

| 50-74 | Needs Improvement | Address warnings this week |

| 25-49 | Poor | Immediate action required |

| 0-24 | Critical | Pause and rebuild |



\### Best Practices

\- ✅ Run comprehensive audits weekly for active campaigns

\- ✅ Use "quick" audits for daily monitoring

\- ✅ Audit before major budget increases

\- ✅ Compare health scores month-over-month for trends

\- ⚠️ Don't over-optimize based on single audit

\- ⚠️ Consider external factors (holidays, news events)

\- ⚠️ Use in combination with Budget Pacing Monitor



\---



\## Contact Information



\### Maintainer

\*\*StationOne Product Team\*\*  

Email: support@stationone.ai  



\---



\*\*Version:\*\* 1.0.1  

\*\*Last Updated:\*\* June 2026  

\*\*License:\*\* Proprietary  

\*\*Skill Package:\*\* `campaign-health-auditor-v1.0.1.zip`

