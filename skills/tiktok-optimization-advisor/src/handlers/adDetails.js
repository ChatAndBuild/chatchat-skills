const TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3";

export async function handleGetAdDetails(args) {
  const { advertiser_id, campaign_ids, adgroup_ids, ad_ids } = args;

  const queryParams = {
    advertiser_id,
    campaign_ids: JSON.stringify(campaign_ids),
    fields: JSON.stringify([
      "ad_id", "ad_name", "adgroup_id", "campaign_id",
      "ad_format", "video_id", "image_ids",
      "call_to_action", "call_to_action_id",
      "landing_page_url", "display_name",
      "spark_ad_type", "item_stitch_status",
      "operation_status", "create_time", "modify_time",
    ]),
  };

  if (adgroup_ids?.length) {
    queryParams.adgroup_ids = JSON.stringify(adgroup_ids);
  }
  if (ad_ids?.length) {
    queryParams.ad_ids = JSON.stringify(ad_ids);
  }

  const params = new URLSearchParams(queryParams);

  const response = await fetch(`${TIKTOK_API_BASE}/ad/get/?${params}`, {
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
