const TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3";

export async function handleGetReporting(args) {
  const {
    advertiser_id,
    campaign_ids,
    level,
    start_date,
    end_date,
    metrics = [
      "spend", "budget", "impressions", "reach", "frequency",
      "clicks", "ctr", "cpm", "cpc", "cpv",
      "video_play_actions", "video_watched_2s", "video_watched_6s",
      "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100",
      "conversions", "cost_per_conversion", "conversion_rate",
      "likes", "comments", "shares", "follows",
    ],
  } = args;

  const params = new URLSearchParams({
    advertiser_id,
    report_type: "BASIC",
    dimensions: JSON.stringify(["campaign_id"]),
    metrics: JSON.stringify(metrics),
    data_level: level,
    start_date,
    end_date,
    filtering: JSON.stringify([
      { field_name: "campaign_ids", filter_type: "IN", filter_value: JSON.stringify(campaign_ids) },
    ]),
    page_size: "100",
  });

  const response = await fetch(`${TIKTOK_API_BASE}/report/integrated/get/?${params}`, {
    headers: {
      "Access-Token": process.env.TIKTOK_ACCESS_TOKEN,
      "Content-Type": "application/json",
    },
  });

  const data = await response.json();

  if (data.code !== 0) {
    throw new Error(`TikTok API error ${data.code}: ${data.message}`);
  }

  return {
    content: [{ type: "text", text: JSON.stringify(data.data, null, 2) }],
  };
}
