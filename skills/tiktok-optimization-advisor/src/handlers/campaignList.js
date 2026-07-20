const TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3";

const STATUS_MAP = {
  ACTIVE: "CAMPAIGN_STATUS_ENABLE",
  PAUSED: "CAMPAIGN_STATUS_DISABLE",
  ALL: "CAMPAIGN_STATUS_ALL",
};

export async function handleListCampaigns(args) {
  const { advertiser_id, status = "ACTIVE", page = 1, page_size = 20 } = args;

  const params = new URLSearchParams({
    advertiser_id,
    primary_status: STATUS_MAP[status] ?? STATUS_MAP.ACTIVE,
    page: String(page),
    page_size: String(page_size),
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
