const TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3";

export async function handleGetCampaignDetails(args) {
  const { advertiser_id, campaign_ids } = args;

  const params = new URLSearchParams({
    advertiser_id,
    campaign_ids: JSON.stringify(campaign_ids),
    fields: JSON.stringify([
      "campaign_id", "campaign_name", "objective_type",
      "budget_mode", "budget", "bid_type",
      "campaign_product_source", "smart_creative_status",
      "operation_status", "create_time", "modify_time",
    ]),
  });

  const response = await fetch(`${TIKTOK_API_BASE}/campaign/get/?${params}`, {
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
