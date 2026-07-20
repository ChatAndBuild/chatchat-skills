\# TikTok Budget Pacing Monitor



\*\*Real-time budget tracking and forecasting agent that monitors budget consumption, identifies pacing issues, and recommends or implements budget adjustments to ensure optimal delivery.\*\*



\---



\## Quick Start



\### Installation

1\. Add this Skill to your StationOne workspace or other AI toolkit from Anthropic, OpenAI or Google

2\. Ensure the \*\*TikTok for Business Connector\*\* is enabled and authenticated

3\. Activate the "TikTok Budget Pacing Monitor" skill



\### Basic Usage

```

"Check pacing for all my June campaigns. I have $100k to spend this 

month and we're on day 18. Am I on track?"

```



The Skill will:

\- Calculate pacing variance for all active campaigns

\- Identify over-pacing and under-pacing entities

\- Forecast month-end delivery

\- Provide budget adjustment recommendations



\---



\## Target Platform



\*\*Compatible with:\*\*

\- ✅ StationOne (primary platform)

\- ✅ Claude (Anthropic)

\- ✅ ChatGPT (OpenAI)

\- ✅ Gemini (Google)



\*\*Platform-specific notes:\*\*

\- Best performance on StationOne with automated daily monitoring

\- Manual refresh required on non-StationOne platforms

\- Visual dashboards only available in StationOne



\---



\## Prerequisites / Dependencies



\### Required

\- \*\*TikTok for Business MCP Connector\*\* (authenticated)

\- Valid TikTok Ads account with Advertiser ID

\- API access with the following permissions:

&#x20; - `campaign.read`

&#x20; - `adgroup.read`

&#x20; - `adgroup.write` (if budget auto-adjustments enabled)

&#x20; - `reporting.read`



\### Runtime Environment

\- No local dependencies

\- Cloud-based execution via StationOne or compatible AI platform

\- Minimum monitoring period: 1 day (3+ days recommended for accuracy)



\### Additional MCPs

\- \*\*None required\*\* - operates exclusively with TikTok for Business MCP

\- Optional: Calendar MCP for scheduled pacing checks (not required)



\---



\## Configuration



\### Default Settings

```yaml

monitoring\_mode: manual                  # Options: manual | scheduled\_daily

pacing\_tolerance: 0.10                   # ±10% variance before alert

date\_range: current\_month                # Options: current\_month | custom\_range

auto\_adjust\_enabled: false               # Require manual approval for changes

max\_budget\_increase: 2.0                 # Cap budget increases at 2x

alert\_threshold\_critical: 0.20           # >20% variance = critical alert

alert\_threshold\_warning: 0.10            # 10-20% variance = warning

```



\### Configurable Parameters



| Parameter | Description | Default | Valid Range |

|-----------|-------------|---------|-------------|

| `monitoring\_period` | Timeframe to analyze | current\_month | current\_month, last\_30\_days, custom |

| `pacing\_tolerance` | Acceptable variance % | 10% | 5% - 25% |

| `budget\_type` | Budget level to monitor | both | campaign, adgroup, both |

| `forecast\_method` | Projection calculation | linear | linear, weighted\_average |

| `notification\_frequency` | Alert cadence | daily | daily, weekly, real\_time |

| `excluded\_campaigns` | Campaign IDs to ignore | \[] | Array of campaign IDs |



\### Environment Variables

```

TIKTOK\_ADVERTISER\_ID=<your\_advertiser\_id>

MONTHLY\_BUDGET\_CAP=100000

PACING\_TOLERANCE=0.10

ALERT\_EMAIL=team@company.com

```



\---



\## Common Errors and Troubleshooting



\### Error: "Unable to calculate pacing - invalid date range"

\*\*Cause:\*\* Campaign start date is in the future or end date has passed  

\*\*Solution:\*\*

\- Verify campaign schedule via TikTok Ads Manager

\- For lifetime budgets, ensure campaign is currently active

\- Check if campaign was paused mid-flight



\### Warning: "Pacing calculation unreliable - insufficient spend"

\*\*Cause:\*\* Campaign has spent <$50 or has <2 days of data  

\*\*Solution:\*\*

\- Wait 24-48 hours for more spend to accumulate

\- Lower `min\_spend\_threshold` in configuration

\- This warning is informational; pacing is still calculated



\### Error: "Forecast unavailable for lifetime budget campaigns"

\*\*Cause:\*\* Campaign end date is not set or is >365 days away  

\*\*Solution:\*\*

\- Set a specific end date in TikTok Ads Manager

\- For evergreen campaigns, use daily budget monitoring instead

\- Manually specify end date in Skill configuration



\### Alert: "Critical over-pacing detected"

\*\*Cause:\*\* Campaign is spending >20% faster than planned pace  

\*\*Action Required:\*\*

1\. Review campaign for sudden performance spikes

2\. Check if bids were recently increased

3\. Implement recommended budget reduction or pause campaign

4\. Monitor for next 24 hours to confirm trend



\### Error: "Budget adjustment failed - insufficient account balance"

\*\*Cause:\*\* TikTok account balance cannot support increased budget  

\*\*Solution:\*\*

\- Add funds to TikTok Ads account

\- Reduce budget increase recommendation

\- Reallocate budget from over-pacing campaigns



\---



\## Limitations and Caveats



\### Known Limitations

1\. \*\*Intraday Fluctuations\*\*: Pacing calculations use daily totals; intraday spending spikes may cause temporary false alerts

2\. \*\*Timezone Dependencies\*\*: All calculations based on advertiser account timezone (not adjustable)

3\. \*\*Lifetime Budget Complexity\*\*: Campaigns with multiple schedule changes may show incorrect pacing

4\. \*\*Smart+ Budget Control\*\*: Limited ability to adjust Smart+ campaign budgets (TikTok algorithm managed)



\### Edge Cases

\- \*\*Campaign Pauses\*\*: If campaign was paused mid-period, pacing calculations may be skewed

\- \*\*Budget Changes\*\*: Historical budget modifications are factored in, but rapid changes (>3 per week) reduce accuracy

\- \*\*Seasonal Spikes\*\*: Holiday shopping days may show critical over-pacing that is intentional

\- \*\*Learning Phase Impact\*\*: New campaigns may underspend in first 3-5 days (not a pacing issue)



\### Best Practices

\- ✅ Monitor pacing weekly for most campaigns

\- ✅ Daily monitoring recommended for campaigns >$5k/day spend

\- ✅ Set tighter tolerance (±5%) for high-budget campaigns

\- ✅ Use `scheduled\_daily` mode for proactive alerts

\- ⚠️ Don't auto-adjust budgets during first week of new campaigns

\- ⚠️ Exclude evergreen/brand campaigns from pacing alerts

\- ⚠️ Cross-reference with Budget Pacing before major budget changes



\---



\## Contact Information



\### Maintainer

\*\*StationOne Product Team\*\*  

Email: support@stationone.ai  



\---



\*\*Version:\*\* 1.0.1  

\*\*Last Updated:\*\* June 2026  

\*\*License:\*\* Proprietary  

\*\*Skill Package:\*\* `budget-pacing-monitor-v1.0.1.zip`

