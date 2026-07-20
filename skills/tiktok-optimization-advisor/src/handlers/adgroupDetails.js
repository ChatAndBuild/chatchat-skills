const TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3";

export async function handleGetAdgroupDetails(args) {
  const { advertiser_id, campaign_ids, adgroup_ids } = args;

  const queryParams = {
    advertiser_id,
    campaign_ids: JSON.stringify(campaign_ids),
    fields: JSON.stringify([
      "adgroup_id", "adgroup_name", "campaign_id",
      "budget_mode", "budget", "bid_type", "bid",
      "optimization_goal", "placement_type", "placements",
      "audience_type", "age", "gender", "location_ids",
      "interest_category_ids", "operation_status",
      "frequency", "frequency_schedule", "dayparting",
      "pixel_id", "app_id", "conversion_event",
    ]),
  };

  if (adgroup_ids?.length) {
    queryParams.adgroup_ids = JSON.stringify(adgroup_ids);
  }

  const params = new URLSearchParams(queryParams);

  const response = await fetch(`${TIKTOK_API_BASE}/adgroup/get/?${params}`, {
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
