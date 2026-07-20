#!/usr/bin/env node
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const CORE_METRICS = {
  spend: { label: "Spend", format: "currency", direction: "neutral", role: "scale" },
  impressions: { label: "Impressions", format: "number", direction: "neutral", role: "scale" },
  clicks: { label: "Clicks", format: "number", direction: "neutral", role: "traffic" },
  conversion: { label: "Conversions", format: "number", direction: "higher", role: "outcome" },
  video_play_actions: { label: "Video Plays", format: "number", direction: "neutral", role: "scale" },
  video_watched_2s: { label: "2s Video Views", format: "number", direction: "neutral", role: "scale" },
  video_watched_6s: { label: "6s Video Views", format: "number", direction: "neutral", role: "scale" },
  video_views_p25: { label: "Video 25%", format: "number", direction: "higher", role: "engagement" },
  video_views_p50: { label: "Video 50%", format: "number", direction: "higher", role: "engagement" },
  video_views_p75: { label: "Video 75%", format: "number", direction: "higher", role: "engagement" },
  video_views_p100: { label: "Video 100%", format: "number", direction: "higher", role: "engagement" },
  profile_visits: { label: "Profile Visits", format: "number", direction: "higher", role: "engagement" },
  follows: { label: "Follows", format: "number", direction: "higher", role: "engagement" },
  likes: { label: "Likes", format: "number", direction: "higher", role: "engagement" },
  comments: { label: "Comments", format: "number", direction: "higher", role: "engagement" },
  shares: { label: "Shares", format: "number", direction: "higher", role: "engagement" },
};

const DERIVED_METRICS = {
  cpc: {
    label: "CPC",
    direction: "lower",
    role: "efficiency",
    format: "currency",
    eligible: (r) => r.spend > 0 && r.clicks > 0,
    value: (r) => r.spend / r.clicks,
    current: (r) => (r.spend > 0 && r.clicks > 0 ? r.spend / r.clicks : null),
    blended: (t) => (t.spend > 0 && t.clicks > 0 ? t.spend / t.clicks : null),
  },
  cost_per_conversion: {
    label: "CPA",
    direction: "lower",
    role: "efficiency",
    format: "currency",
    eligible: (r) => r.spend > 0 && r.conversion > 0,
    value: (r) => r.spend / r.conversion,
    current: (r) => (r.spend > 0 && r.conversion > 0 ? r.spend / r.conversion : null),
    blended: (t) => (t.spend > 0 && t.conversion > 0 ? t.spend / t.conversion : null),
  },
  cpm: {
    label: "CPM",
    direction: "lower",
    role: "efficiency",
    format: "currency",
    eligible: (r) => r.spend > 0 && r.impressions > 0,
    value: (r) => (r.spend / r.impressions) * 1000,
    current: (r) => (r.spend > 0 && r.impressions > 0 ? (r.spend / r.impressions) * 1000 : null),
    blended: (t) => (t.spend > 0 && t.impressions > 0 ? (t.spend / t.impressions) * 1000 : null),
  },
  ctr: {
    label: "CTR",
    direction: "higher",
    role: "rate",
    format: "percent",
    eligible: (r) => r.impressions > 0,
    value: (r) => (r.clicks / r.impressions) * 100,
    current: (r) => (r.impressions > 0 ? (r.clicks / r.impressions) * 100 : null),
    blended: (t) => (t.impressions > 0 ? (t.clicks / t.impressions) * 100 : null),
  },
  conversion_rate: {
    label: "CVR",
    direction: "higher",
    role: "outcome",
    format: "percent",
    eligible: (r) => r.clicks > 0,
    value: (r) => (r.conversion / r.clicks) * 100,
    current: (r) => (r.clicks > 0 ? (r.conversion / r.clicks) * 100 : null),
    blended: (t) => (t.clicks > 0 ? (t.conversion / t.clicks) * 100 : null),
  },
};

const ALIASES = {
  cpa: "cost_per_conversion",
  cvr: "conversion_rate",
  conversions: "conversion",
};

const ADS_MANAGER_COLUMNS = [
  "campaign_budget",
  "ad_id",
  "budget",
  "bid",
  "schedule",
  "attribution_window",
  "attribution_statistic_type",
  "ad_name",
  "creative_id",
  "po_number",
  "stat_cost",
  "cpc",
  "cpm",
  "show_cnt",
  "click_cnt",
  "ctr",
  "time_attr_convert_cnt",
  "skan_convert_cnt",
  "time_attr_conversion_cost",
  "skan_conversion_cost",
  "time_attr_conversion_rate",
  "time_attr_conversion_rate_imp",
  "skan_conversion_rate",
  "skan_conversion_rate_imp",
  "time_attr_effect_cnt",
  "time_attr_effect_cost",
  "time_attr_effect_rate",
  "time_attr_deep_convert_cnt_v2",
  "time_attr_cost_per_deep_convert_v2",
  "time_attr_deep_convert_rate_v2",
];

const LINK_KINDS = {
  campaign: { route: "campaign", field: "campaign_ids", grain: "Campaign", idField: "campaign_id" },
  adgroup: { route: "adgroup", field: "ad_ids", grain: "AdGroup", idField: "adgroup_link_id" },
  creative: { grain: "Creative" },
  smart_plus_creative: { grain: "Creative" },
};

function usage() {
  console.error(`Usage:
  node scripts/compute-account-benchmark.mjs \\
    --analysis raw-analysis.json \\
    --benchmark raw-benchmark.json \\
    --analysis-id 1234567890 \\
    --metrics spend,cpc,ctr \\
    --analysis-label "2026-06-01 to 2026-06-07 · Campaign level" \\
    --benchmark-label "2026-05-09 to 2026-06-06"

Options:
  --analysis-id <id>          Required when the analysis report has multiple rows
  --metrics <csv>             Metric keys to compute. Default: cpc,cost_per_conversion,cpm,ctr,conversion_rate
  --analysis-days <number>    Used to normalize additive metrics to daily values. Default: 1
  --benchmark-days <number>   Used to normalize additive metrics to daily values. Default: 1
  --cost-active-min <number>  Minimum spend for benchmark pool. Default: 0
  --objective-field <key>     Optional row field used to filter the benchmark pool by objective
  --objective-type <value>    Optional objective value required for the benchmark pool
  --advertiser-id <id>        Enables Ads Manager object links with this advertiser ID
  --link-kind <kind>          campaign|adgroup|creative|smart_plus_creative|auto. Default: auto.
                              Ad/Creative grains render plain object names without Ads Manager links.
  --start-date <YYYY-MM-DD>   Ads Manager link start date
  --end-date <YYYY-MM-DD>     Ads Manager link end date
  --relative-time <value>     Deprecated compatibility flag; object links use st/et only
  --format <markdown|json>    Default: markdown
  --language <en|zh>          Markdown output language. Default: zh
`);
}

function parseArgs(argv) {
  const args = {
    costActiveMin: 0,
    format: "markdown",
    analysisLabel: "analysis window",
    benchmarkLabel: "benchmark window",
    analysisDays: 1,
    benchmarkDays: 1,
    metricKeys: ["cpc", "cost_per_conversion", "cpm", "ctr", "conversion_rate"],
    language: "zh",
    linkKind: "auto",
    relativeTime: "last_7_days",
  };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    const val = argv[i + 1];
    if (key === "--analysis") args.analysis = val, i += 1;
    else if (key === "--benchmark") args.benchmark = val, i += 1;
    else if (key === "--analysis-id") args.analysisId = val, i += 1;
    else if (key === "--analysis-label") args.analysisLabel = val, i += 1;
    else if (key === "--benchmark-label") args.benchmarkLabel = val, i += 1;
    else if (key === "--analysis-days") args.analysisDays = Number(val), i += 1;
    else if (key === "--benchmark-days") args.benchmarkDays = Number(val), i += 1;
    else if (key === "--metrics") args.metricKeys = val.split(",").map((item) => item.trim()).filter(Boolean), i += 1;
    else if (key === "--cost-active-min") args.costActiveMin = Number(val), i += 1;
    else if (key === "--objective-field") args.objectiveField = val, i += 1;
    else if (key === "--objective-type") args.objectiveType = val, i += 1;
    else if (key === "--advertiser-id") args.advertiserId = val, i += 1;
    else if (key === "--link-kind") args.linkKind = normalizeLinkKind(val), i += 1;
    else if (key === "--start-date") args.startDate = val, i += 1;
    else if (key === "--end-date") args.endDate = val, i += 1;
    else if (key === "--relative-time") args.relativeTime = val, i += 1;
    else if (key === "--format") args.format = val, i += 1;
    else if (key === "--language") args.language = val, i += 1;
    else if (key === "--help" || key === "-h") args.help = true;
    else throw new Error(`Unknown argument: ${key}`);
  }
  if (!["en", "zh"].includes(args.language)) throw new Error(`Unsupported language: ${args.language}`);
  if (!["campaign", "adgroup", "creative", "smart_plus_creative", "auto"].includes(args.linkKind)) throw new Error(`Unsupported link kind: ${args.linkKind}`);
  return args;
}

function normalizeLinkKind(value) {
  if (value === "ad") return "creative";
  if (["smart-plus-creative", "smart_plus", "splus_creative", "splus"].includes(value)) return "smart_plus_creative";
  return value;
}

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return JSON.parse(raw);
}

export function unwrapReport(input) {
  // Accept raw TikTok response, MCP text response, or an array of MCP content blocks.
  if (Array.isArray(input) && input.length === 1 && input[0]?.type === "text") {
    return unwrapReport(JSON.parse(input[0].text));
  }
  if (input?.type === "text" && typeof input.text === "string") {
    return unwrapReport(JSON.parse(input.text));
  }
  if (input?.data?.list) return input.data;
  if (input?.list) return input;
  throw new Error("Unsupported report shape: expected TikTok report data.list");
}

function normalizeMetricKey(key) {
  return ALIASES[key] || key;
}

function toNumber(value) {
  if (value === undefined || value === null || value === "-") return 0;
  const n = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function toStringOrEmpty(value) {
  if (value === undefined || value === null || value === "") return "";
  return String(value);
}

export function normalizeRows(report) {
  return report.list.map((row) => {
    const metrics = row.metrics ?? {};
    const dimensions = row.dimensions ?? {};
    const normalized = {};
    for (const [key, value] of Object.entries(metrics)) normalized[key] = toNumber(value);
    const campaignId = toStringOrEmpty(dimensions.campaign_id ?? metrics.campaign_id ?? row.campaign_id);
    const adgroupId = toStringOrEmpty(dimensions.adgroup_id ?? metrics.adgroup_id ?? row.adgroup_id);
    const adId = toStringOrEmpty(dimensions.ad_id ?? metrics.ad_id ?? row.ad_id);
    const creativeId = toStringOrEmpty(dimensions.creative_id ?? metrics.creative_id ?? row.creative_id);
    const smartPlusAdId = toStringOrEmpty(
      dimensions.smart_plus_ad_id
        ?? metrics.smart_plus_ad_id
        ?? row.smart_plus_ad_id,
    );
    const virtualCreativeId = toStringOrEmpty(
      dimensions.virtual_creative_id
        ?? metrics.virtual_creative_id
        ?? row.virtual_creative_id,
    );
    const adgroupLinkId = adgroupId || adId;
    const creativeLinkId = adId || smartPlusAdId;
    const smartPlusCreativeLinkId = virtualCreativeId || smartPlusAdId;
    const advertiserId = toStringOrEmpty(dimensions.advertiser_id ?? metrics.advertiser_id ?? row.advertiser_id);
    const id = adId || adgroupId || campaignId || smartPlusAdId || advertiserId || "unknown";
    const nameCandidate = metrics.ad_name ?? metrics.adgroup_name ?? metrics.campaign_name ?? row.ad_name ?? row.adgroup_name ?? row.campaign_name;
    const nameFieldAvailable = nameCandidate !== undefined && nameCandidate !== null && String(nameCandidate).trim() !== "";
    return {
      ...normalized,
      id,
      campaign_id: campaignId,
      adgroup_id: adgroupId,
      ad_id: adId,
      creative_id: creativeId,
      smart_plus_ad_id: smartPlusAdId,
      virtual_creative_id: virtualCreativeId,
      adgroup_link_id: adgroupLinkId,
      creative_link_id: creativeLinkId,
      smart_plus_creative_link_id: smartPlusCreativeLinkId,
      advertiser_id: advertiserId,
      name: nameFieldAvailable ? String(nameCandidate) : "Unknown name",
      nameFieldAvailable,
      objective_type: String(metrics.objective_type ?? dimensions.objective_type ?? ""),
      campaign_type: String(metrics.campaign_type ?? dimensions.campaign_type ?? ""),
      spend: toNumber(metrics.spend),
      impressions: toNumber(metrics.impressions),
      clicks: toNumber(metrics.clicks),
      conversion: toNumber(metrics.conversion ?? metrics.conversions),
    };
  });
}

function selectAnalysisTarget(rows, analysisId) {
  if (analysisId) {
    const row = rows.find((item) => item.id === String(analysisId));
    if (!row) throw new Error(`Analysis target not found: ${analysisId}`);
    return row;
  }
  if (rows.length === 1) return rows[0];
  throw new Error("Analysis report has multiple rows. Pass --analysis-id to select one target.");
}

function totals(rows) {
  return rows.reduce((acc, row) => {
    const keys = new Set([...Object.keys(acc), ...Object.keys(row)]);
    for (const key of keys) {
      if (typeof acc[key] === "number" || typeof row[key] === "number") {
        acc[key] = toNumber(acc[key]) + toNumber(row[key]);
      }
    }
    return acc;
  }, { spend: 0, impressions: 0, clicks: 0, conversion: 0 });
}

function percentile(values, p) {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  const weight = idx - lo;
  return sorted[lo] * (1 - weight) + sorted[hi] * weight;
}

function percentileRank(values, current, direction) {
  if (current === null || current === undefined || !Number.isFinite(current) || values.length === 0) return null;
  const betterOrEqual = direction === "lower"
    ? values.filter((value) => value >= current).length
    : values.filter((value) => value <= current).length;
  return Number(((betterOrEqual / values.length) * 100).toFixed(2));
}

function average(values) {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function confidence(n) {
  if (n === 0) return "unavailable";
  if (n < 10) return "low";
  if (n < 30) return "medium";
  return "high";
}

function fmt(value, format) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "-";
  if (format === "currency") return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (format === "percent") return `${value.toFixed(2)}%`;
  return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function verdict(current, median, def) {
  if (current === null || median === null) return "Unavailable";
  const delta = (current - median) / Math.abs(median || 1);
  if (Math.abs(delta) < 0.05) return "Near median";
  const pct = Math.abs(delta * 100).toFixed(0);
  if (def.direction === "neutral") {
    return current > median ? `${pct}% higher than median` : `${pct}% lower than median`;
  }
  const better = def.direction === "lower" ? current < median : current > median;
  return better ? `${pct}% better than median` : `${pct}% worse than median`;
}

function relativePosition(metric) {
  if (metric.percentileRank === null || metric.percentileRank === undefined) return "-";
  if (metric.direction !== "neutral" && metric.percentileRank <= 0) return "Worse than most comparable objects";
  if (metric.direction !== "neutral" && metric.percentileRank >= 100) return "Better than nearly all comparable objects";
  if (metric.direction === "neutral" && metric.percentileRank <= 0) return "Lower than most comparable objects";
  if (metric.direction === "neutral" && metric.percentileRank >= 100) return "Higher than nearly all comparable objects";
  if (metric.direction === "neutral") return `Higher than ${metric.percentileRank}% of comparable objects`;
  if (metric.percentileRank >= 50) return `Better than ${metric.percentileRank}% of comparable objects`;
  return `Worse than ${Number((100 - metric.percentileRank).toFixed(2))}% of comparable objects`;
}

function relativePositionText(metric, language = "en") {
  if (language !== "zh") return metric.positionLabel || relativePosition(metric);
  if (metric.percentileRank === null || metric.percentileRank === undefined) return "-";
  if (metric.direction === "neutral") {
    if (metric.percentileRank <= 0) return "低于大多数可比对象";
    if (metric.percentileRank >= 100) return "高于几乎所有可比对象";
    const n = `${metric.percentileRank}%`;
    return `高于 ${n} 的可比对象`;
  }
  if (metric.percentileRank <= 0) return "弱于大多数可比对象";
  if (metric.percentileRank >= 100) return "优于几乎所有可比对象";
  if (metric.percentileRank >= 50) return `优于 ${metric.percentileRank}% 的可比对象`;
  return `差于 ${Number((100 - metric.percentileRank).toFixed(2))}% 的可比对象`;
}

function verdictText(metric, language = "en") {
  if (language !== "zh") return metric.verdict;
  if (metric.current === null || metric.current === undefined || metric.p50 === null || metric.p50 === undefined) {
    return "不可判断";
  }
  const delta = (metric.current - metric.p50) / Math.abs(metric.p50 || 1);
  if (Math.abs(delta) < 0.05) {
    return "接近中位数";
  }
  const pct = Math.abs(delta * 100).toFixed(0);
  if (metric.direction === "neutral") {
    return metric.current > metric.p50 ? `比中位数高 ${pct}%` : `比中位数低 ${pct}%`;
  }
  const better = metric.direction === "lower" ? metric.current < metric.p50 : metric.current > metric.p50;
  return better ? `比中位数好 ${pct}%` : `比中位数差 ${pct}%`;
}

function metricLabel(metric, language = "en") {
  if (language !== "zh") return metric.label;
  const labels = {
    Spend: "消耗",
    Impressions: "展示",
    Clicks: "点击",
    Conversions: "转化",
    "Video Plays": "视频播放",
    "2s Video Views": "2 秒播放",
    "6s Video Views": "6 秒播放",
    "Video 25%": "视频 25%",
    "Video 50%": "视频 50%",
    "Video 75%": "视频 75%",
    "Video 100%": "视频完播",
    "Profile Visits": "主页访问",
    Follows: "关注",
    Likes: "点赞",
    Comments: "评论",
    Shares: "分享",
  };
  return labels[metric.label] || metric.label;
}

function inferLinkKind(row, requested = "auto") {
  if (isSmartPlusCreativeRow(row) && (!requested || requested === "auto" || requested === "creative" || requested === "ad")) {
    return "smart_plus_creative";
  }
  if (requested && requested !== "auto") return requested;
  if (row.ad_id) return "creative";
  if (row.adgroup_id) return "adgroup";
  if (row.campaign_id) return "campaign";
  return "campaign";
}

function isSmartPlusCreativeRow(row) {
  return Boolean(
    row.virtual_creative_id
      || row.smart_plus_ad_id
      || /SMART|UPGRADED_SMART_PLUS/i.test(row.campaign_type || ""),
  );
}

function grainLabel(row, args) {
  return LINK_KINDS[inferLinkKind(row, args.linkKind)]?.grain || "Object";
}

function markdownLinkLabel(value) {
  return String(value).replace(/\\/g, "\\\\").replace(/\[/g, "\\[").replace(/\]/g, "\\]");
}

function objectLinkState(row, args) {
  const kind = inferLinkKind(row, args.linkKind);
  if (kind === "creative" || kind === "smart_plus_creative") {
    return { kind, url: "", reason: "ad grain links disabled", disabled: true };
  }
  const config = LINK_KINDS[kind];
  if (!config) return { kind, url: "", reason: "unsupported link kind" };
  if (!args.advertiserId) return { kind, url: "", reason: "missing advertiser_id" };
  const objectId = row[config.idField];
  if (!objectId) return { kind, url: "", reason: `missing ${config.idField}` };

  const params = new URLSearchParams();
  params.set("aadvid", args.advertiserId);
  params.set("navigate_from", "campaignList");
  params.set("columns", ADS_MANAGER_COLUMNS.join(","));
  if (args.startDate) params.set("st", args.startDate);
  if (args.endDate) params.set("et", args.endDate);
  params.set("filters[0][field]", config.field);
  params.set("filters[0][filter_type]", "0");
  params.set("filters[0][in_field_values][0]", objectId);
  if (config.includeSource !== false) params.set("filters[0][source]", "sidebar");
  return {
    kind,
    field: config.field,
    objectId,
    url: `https://ads.tiktok.com/i18n/manage/${config.route}?${params.toString()}`,
    reason: "",
  };
}

function objectLabel(row, args) {
  const label = row.nameFieldAvailable ? row.name : "Unknown name";
  const link = objectLinkState(row, args);
  return link.url ? `[${markdownLinkLabel(label)}](${link.url})` : label;
}

function primaryVerdictMetric(metrics) {
  const priority = ["cost_per_conversion", "conversion_rate", "cpc", "ctr", "cpm"];
  for (const key of priority) {
    const metric = metrics.find((item) => item.key === key && item.direction !== "neutral");
    if (metric) return metric;
  }
  return metrics.find((metric) => metric.direction !== "neutral") || metrics[0] || null;
}

function qualitativeRead(metric, language = "en") {
  if (!metric || metric.percentileRank === null || metric.percentileRank === undefined) {
    return language === "zh" ? "暂不可判断" : "unavailable";
  }
  if (metric.direction === "neutral") {
    if (metric.percentileRank >= 70) return language === "zh" ? "规模偏高" : "high scale";
    if (metric.percentileRank <= 30) return language === "zh" ? "规模偏低" : "low scale";
    return language === "zh" ? "规模接近中位数" : "near median scale";
  }
  if (metric.percentileRank >= 70) return language === "zh" ? "表现强" : "strong";
  if (metric.percentileRank <= 30) return language === "zh" ? "表现弱" : "weak";
  return language === "zh" ? "表现接近中位数" : "near median";
}

function compactMetricBullets(metrics, language = "en") {
  return metrics.map((metric) => {
    const label = metricLabel(metric, language);
    const current = fmt(metric.current, metric.format);
    const medianValue = fmt(metric.p50, metric.format);
    const position = relativePositionText(metric, language);
    return language === "zh"
      ? `- ${label}：当前 ${current}；中位数 ${medianValue}；${position}。`
      : `- ${label}: current ${current}; median ${medianValue}; ${position}.`;
  });
}

function rawMetricDefinition(key, options) {
  const meta = CORE_METRICS[key] || { label: key, format: "number", direction: "higher" };
  const analysisDays = Math.max(1, Number(options.analysisDays || 1));
  const benchmarkDays = Math.max(1, Number(options.benchmarkDays || 1));
  const hasMetric = (row) => Object.hasOwn(row, key);
  return {
    key,
    label: analysisDays === benchmarkDays ? meta.label : `${meta.label} / day`,
    direction: meta.direction,
    role: meta.role || "scale",
    format: meta.format,
    eligible: hasMetric,
    value: (row) => (hasMetric(row) ? toNumber(row[key]) / benchmarkDays : Number.NaN),
    current: (row) => (hasMetric(row) ? toNumber(row[key]) / analysisDays : null),
    blended: (_totals, rows) => average(rows.filter(hasMetric).map((row) => toNumber(row[key]) / benchmarkDays)),
  };
}

function metricDefinition(key, options) {
  const normalizedKey = normalizeMetricKey(key);
  if (DERIVED_METRICS[normalizedKey]) return { key: normalizedKey, ...DERIVED_METRICS[normalizedKey] };
  return rawMetricDefinition(normalizedKey, options);
}

function compute(analysisTarget, benchmarkRows, options = {}) {
  const costActiveMin = Number(options.costActiveMin ?? 0);
  const metricKeys = [...new Set((options.metricKeys || []).map(normalizeMetricKey))];
  const objectiveField = options.objectiveField || null;
  const objectiveType = options.objectiveType || null;
  const objectiveFilteredRows = objectiveField && objectiveType
    ? benchmarkRows.filter((row) => String(row[objectiveField] ?? "") === String(objectiveType))
    : benchmarkRows;
  const costActiveRows = objectiveFilteredRows.filter((row) => row.spend > costActiveMin);
  const benchmarkTotals = totals(costActiveRows);
  const zeroConversionCostActive = costActiveRows.filter((row) => row.conversion === 0).length;

  const metrics = metricKeys.map((key) => {
    const def = metricDefinition(key, options);
    const values = costActiveRows.filter(def.eligible).map(def.value).filter(Number.isFinite);
    const current = def.current(analysisTarget);
    const blended = def.blended(benchmarkTotals, costActiveRows);
    const p25 = percentile(values, 0.25);
    const p50 = percentile(values, 0.5);
    const p75 = percentile(values, 0.75);
    return {
      key: def.key,
      label: def.label,
      direction: def.direction,
      current,
      blended,
      p25,
      p50,
      p75,
      top25: def.direction === "lower" ? p25 : p75,
      percentileRank: percentileRank(values, current, def.direction),
      eligibleSample: values.length,
      confidence: confidence(values.length),
      verdict: verdict(current, p50, def),
      format: def.format,
      role: def.role || "metric",
      positionLabel: relativePosition({ direction: def.direction, percentileRank: percentileRank(values, current, def.direction) }),
    };
  });

  return {
    analysis: {
      target: analysisTarget,
    },
    benchmark: {
      totalRows: benchmarkRows.length,
      objectiveFilteredRows: objectiveFilteredRows.length,
      objectiveField,
      objectiveType,
      costActiveRows: costActiveRows.length,
      excludedRows: benchmarkRows.length - costActiveRows.length,
      excludedByObjective: benchmarkRows.length - objectiveFilteredRows.length,
      zeroConversionCostActive,
      totals: benchmarkTotals,
    },
    metrics,
  };
}

export function computeAccountBenchmark({
  analysisReport,
  benchmarkReport,
  analysisId,
  metricKeys,
  analysisDays = 1,
  benchmarkDays = 1,
  costActiveMin = 0,
  objectiveField,
  objectiveType,
} = {}) {
  const analysis = unwrapReport(analysisReport);
  const benchmark = unwrapReport(benchmarkReport);
  const analysisTarget = selectAnalysisTarget(normalizeRows(analysis), analysisId);
  return compute(analysisTarget, normalizeRows(benchmark), {
    metricKeys,
    analysisDays,
    benchmarkDays,
    costActiveMin,
    objectiveField,
    objectiveType,
  });
}

function escapedRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function validateMarkdownOutput(markdown, result, args) {
  const target = result.analysis.target;
  const grain = grainLabel(target, args);
  const link = objectLinkState(target, args);
  if (/\|\s*ID\s*\|/.test(markdown)) throw new Error("Output validation failed: object tables must not include a standalone ID column.");
  if (/\|\s*(对象|Object)\s*\|/.test(markdown)) throw new Error("Output validation failed: object table header must use the concrete grain, not Object/对象.");
  if (!markdown.includes(`| ${grain} |`)) throw new Error(`Output validation failed: object overview must use '${grain}' as the first column.`);
  if (target.id && target.id !== "unknown" && markdown.includes(`${target.name} (${target.id})`)) {
    throw new Error("Output validation failed: object references must not use the legacy name-plus-ID style.");
  }
  if (link.disabled) {
    const label = target.nameFieldAvailable ? target.name : "Unknown name";
    const linkedLabel = new RegExp(`\\[${escapedRegExp(markdownLinkLabel(label))}\\]\\([^\\n]+\\)`, "g");
    if (linkedLabel.test(markdown)) {
      throw new Error("Output validation failed: Ad-grain object names must render as plain text, not Markdown links.");
    }
    if (
      /https:\/\/ads\.tiktok\.com\/i18n\/manage\/creative/.test(markdown)
      || /filters%5B0%5D%5Bfield%5D=(creative_ids|virtual_creative_id)/.test(markdown)
      || /filters\[0\]\[field\]=(creative_ids|virtual_creative_id)/.test(markdown)
    ) {
      throw new Error("Output validation failed: Ad-grain output must not include Creative Ads Manager links.");
    }
  }
  if (link.url) {
    for (const forbiddenParam of ["relative_time=", "sort_state=", "sort_order="]) {
      if (markdown.includes(forbiddenParam)) {
        throw new Error(`Output validation failed: object links must not include ${forbiddenParam.replace("=", "")}.`);
      }
    }
    if (!markdown.includes("navigate_from=campaignList")) {
      throw new Error("Output validation failed: object links must use navigate_from=campaignList.");
    }
    if (!markdown.includes("columns=")) {
      throw new Error("Output validation failed: object links must include the standard columns parameter.");
    }
    if (!markdown.includes("filters%5B0%5D%5Bfield%5D=") && !markdown.includes("filters[0][field]=")) {
      throw new Error("Output validation failed: object links must use filters[0][field], not shorthand ID parameters.");
    }
    const encodedField = encodeURIComponent(link.field);
    if (
      !markdown.includes(`filters%5B0%5D%5Bfield%5D=${encodedField}`)
      && !markdown.includes(`filters[0][field]=${link.field}`)
    ) {
      throw new Error(`Output validation failed: object link filter field must use ${link.field}.`);
    }
    const encodedLinkId = encodeURIComponent(link.objectId);
    if (
      !markdown.includes(`filters%5B0%5D%5Bin_field_values%5D%5B0%5D=${encodedLinkId}`)
      && !markdown.includes(`filters[0][in_field_values][0]=${link.objectId}`)
    ) {
      throw new Error(`Output validation failed: object link filter must use ${link.kind} link ID ${link.objectId}.`);
    }
    if (/filters%5B0%5D%5Bin_field_values%5D%5B[1-9]\d*%5D=/.test(markdown) || /filters\[0\]\[in_field_values\]\[[1-9]\d*\]=/.test(markdown)) {
      throw new Error("Output validation failed: object links must target one object per link.");
    }
    if (/[?&](campaign_ids|ad_ids|creative_ids)=/.test(markdown)) {
      throw new Error("Output validation failed: object links must not use top-level campaign_ids/ad_ids/creative_ids parameters.");
    }
    const label = target.nameFieldAvailable ? target.name : "Unknown name";
    const linkedLabel = new RegExp(`\\[${escapedRegExp(markdownLinkLabel(label))}\\]\\([^\\n]+\\)`, "g");
    if (!linkedLabel.test(markdown)) throw new Error("Output validation failed: linked object label is missing.");
    if (target.nameFieldAvailable) {
      const withoutLinkedLabels = markdown.replace(linkedLabel, "");
      if (withoutLinkedLabels.includes(target.name)) {
        throw new Error("Output validation failed: known object name appears outside Markdown link syntax.");
      }
    }
  }
}

function renderMarkdown(result, args) {
  const language = args.language || "en";
  const zh = language === "zh";
  const lines = [];
  const target = result.analysis.target;
  const targetLabel = objectLabel(target, args);
  const targetGrain = grainLabel(target, args);
  const targetLinkState = objectLinkState(target, args);
  const verdictMetric = primaryVerdictMetric(result.metrics);
  lines.push(zh ? "# 账号基准摘要" : "# Account Benchmark Summary");
  lines.push("");
  lines.push(zh ? "## 结论先说" : "## Bottom line");
  if (verdictMetric) {
    lines.push(zh
      ? `${targetLabel} ${qualitativeRead(verdictMetric, language)}：${metricLabel(verdictMetric, language)} ${verdictText(verdictMetric, language)}。`
      : `${targetLabel} is ${qualitativeRead(verdictMetric, language)}: ${metricLabel(verdictMetric, language)} is ${verdictText(verdictMetric, language)}.`);
  } else {
    lines.push(zh ? `${targetLabel} 暂不可判断：没有可用指标生成基准结论。` : `${targetLabel} is unavailable: no metric could be used to produce a benchmark verdict.`);
  }
  lines.push("");
  lines.push(...compactMetricBullets(result.metrics, language));
  const importantSamples = result.metrics
    .filter((metric) => ["cost_per_conversion", "conversion_rate", "cpc", "ctr", "cpm"].includes(metric.key))
    .map((metric) => metric.eligibleSample)
    .filter((value) => Number.isFinite(value));
  const minImportantSample = importantSamples.length ? Math.min(...importantSamples) : result.benchmark.costActiveRows;
  if (minImportantSample === 0) {
    lines.push("");
    lines.push(zh
      ? "样本提示：至少一个关键指标没有可比样本，因此不要对该指标下 benchmark 结论。"
      : "Sample caveat: no eligible comparable rows are available for at least one key metric, so no benchmark conclusion should be drawn for that metric.");
  } else if (minImportantSample < 10) {
    lines.push("");
    lines.push(zh
      ? `样本提示：至少一个关键指标只有 ${minImportantSample} 个可比样本。这个结论更适合作为方向性信号，建议用更长窗口或更粗粒度验证。`
      : `Sample caveat: only ${minImportantSample} eligible comparable rows are available for at least one key metric. Treat the result as a directional signal and verify with a longer window or coarser grain.`);
  } else if (minImportantSample < 30) {
    lines.push("");
    lines.push(zh
      ? `样本提示：至少一个关键指标有 ${minImportantSample} 个可比样本，结论具备参考价值；如果要影响投放决策，仍建议用更长窗口验证。`
      : `Sample caveat: ${minImportantSample} eligible comparable rows are available for at least one key metric. The result is useful, but should still be verified with a longer window if it will drive decisions.`);
  }
  lines.push("");
  lines.push(zh ? "## 对象指标概览" : "## Object metric overview");
  lines.push(`| ${targetGrain} | ${result.metrics.map((metric) => metricLabel(metric, language)).join(" | ")} | ${zh ? "定位" : "Position"} |`);
  lines.push(`|---${result.metrics.map(() => "|---:").join("")}|---|`);
  lines.push(`| ${targetLabel} | ${result.metrics.map((metric) => fmt(metric.current, metric.format)).join(" | ")} | ${verdictMetric ? qualitativeRead(verdictMetric, language) : "-"} |`);
  lines.push("");
  lines.push(zh ? "## 核心对比" : "## Benchmark table");
  lines.push(zh
    ? "| 指标 | 当前对象 | 中位数 | 相对位置 | 有效样本 | 业务判断 |"
    : "| Metric | Current | Median | Relative position | Eligible sample | Business read |");
  lines.push("|---|---:|---:|---|---:|---|");
  for (const metric of result.metrics) {
    lines.push(
      `| ${metricLabel(metric, language)} | ${fmt(metric.current, metric.format)} | ${fmt(metric.p50, metric.format)} | ${relativePositionText(metric, language)} | ${metric.eligibleSample} | ${verdictText(metric, language)} |`,
    );
  }
  lines.push("");
  lines.push(zh ? "## 基准结论" : "## Benchmark verdict");
  lines.push(verdictMetric
    ? (zh
      ? `${metricLabel(verdictMetric, language)} 是当前主判断指标；当前 ${fmt(verdictMetric.current, verdictMetric.format)}，中位数 ${fmt(verdictMetric.p50, verdictMetric.format)}，${verdictText(verdictMetric, language)}。`
      : `${metricLabel(verdictMetric, language)} is the primary read: current ${fmt(verdictMetric.current, verdictMetric.format)}, median ${fmt(verdictMetric.p50, verdictMetric.format)}, ${verdictText(verdictMetric, language)}.`)
    : (zh ? "没有可用指标生成基准结论。" : "No available metric could be used to produce a benchmark verdict."));
  lines.push("");
  lines.push(zh ? "## 下一步建议" : "## Next steps");
  lines.push(zh
    ? "以下建议基于报表数据，执行前请结合实时投放状态确认。"
    : "These suggestions are based on report data; confirm current delivery status before acting.");
  lines.push(zh
    ? "- 先复核主判断指标对应的对象状态、预算节奏和样本量，再决定是否进入优化或管理流程。"
    : "- Review current object status, pacing, and sample size for the primary metric before moving into optimization or management.");
  lines.push(zh
    ? "- 如果样本偏小，优先扩大窗口或切到更粗粒度复验。"
    : "- If the sample is small, verify with a longer window or coarser grain first.");
  lines.push("");
  lines.push(zh ? "## 附录：基准范围" : "## Appendix: Benchmark scope");
  lines.push(zh ? `分析窗口：${args.analysisLabel}` : `Analysis window: ${args.analysisLabel}`);
  lines.push(zh ? `基准窗口：${args.benchmarkLabel}` : `Benchmark window: ${args.benchmarkLabel}`);
  lines.push(zh ? `分析对象：${targetLabel}` : `Analysis target: ${targetLabel}`);
  if (!target.nameFieldAvailable) {
    lines.push(zh ? "名称字段不可用：使用 Unknown name 作为兜底展示。" : "Name field unavailable: using Unknown name as the display fallback.");
  }
  if (args.advertiserId && !targetLinkState.url && !targetLinkState.disabled) {
    lines.push(zh
      ? `Partial link state：对象链接未生成，原因是 ${targetLinkState.reason}。`
      : `Partial link state: object link was not generated because ${targetLinkState.reason}.`);
  }
  if (targetLinkState.url && (!args.startDate || !args.endDate)) {
    lines.push(zh
      ? "Partial link state：对象链接已生成，但日期参数不完整；请以实际 benchmark 请求窗口为准。"
      : "Partial link state: object link was generated without a complete date range; use the actual benchmark request window as the source of truth.");
  }
  if (result.benchmark.objectiveField && result.benchmark.objectiveType) {
    lines.push(zh
      ? `目标过滤：${result.benchmark.objectiveField} = ${result.benchmark.objectiveType}`
      : `Objective filter: ${result.benchmark.objectiveField} = ${result.benchmark.objectiveType}`);
  }
  lines.push(zh ? `基准池：spend > ${args.costActiveMin}` : `Benchmark pool: spend > ${args.costActiveMin}`);
  lines.push(zh
    ? `样本：${result.benchmark.costActiveRows} 个有消耗对象 / ${result.benchmark.totalRows} 个总对象（排除 ${result.benchmark.excludedRows} 个）`
    : `Sample: ${result.benchmark.costActiveRows} cost-active rows / ${result.benchmark.totalRows} total rows (${result.benchmark.excludedRows} excluded)`);
  if (result.benchmark.excludedByObjective > 0) {
    lines.push(zh ? `按目标排除对象数：${result.benchmark.excludedByObjective}` : `Objective excluded rows: ${result.benchmark.excludedByObjective}`);
  }
  lines.push(zh ? `有消耗但 0 转化对象数：${result.benchmark.zeroConversionCostActive}` : `Zero-conversion cost-active rows: ${result.benchmark.zeroConversionCostActive}`);
  lines.push(zh
    ? `分析对象汇总：消耗 ${fmt(result.analysis.target.spend, "currency")}，展示 ${Math.round(result.analysis.target.impressions).toLocaleString()}，点击 ${Math.round(result.analysis.target.clicks).toLocaleString()}，转化 ${Math.round(result.analysis.target.conversion).toLocaleString()}`
    : `Analysis target totals: spend ${fmt(result.analysis.target.spend, "currency")}, impressions ${Math.round(result.analysis.target.impressions).toLocaleString()}, clicks ${Math.round(result.analysis.target.clicks).toLocaleString()}, conversions ${Math.round(result.analysis.target.conversion).toLocaleString()}`);
  lines.push(zh
    ? `基准汇总：消耗 ${fmt(result.benchmark.totals.spend, "currency")}，展示 ${Math.round(result.benchmark.totals.impressions).toLocaleString()}，点击 ${Math.round(result.benchmark.totals.clicks).toLocaleString()}，转化 ${Math.round(result.benchmark.totals.conversion).toLocaleString()}`
    : `Benchmark totals: spend ${fmt(result.benchmark.totals.spend, "currency")}, impressions ${Math.round(result.benchmark.totals.impressions).toLocaleString()}, clicks ${Math.round(result.benchmark.totals.clicks).toLocaleString()}, conversions ${Math.round(result.benchmark.totals.conversion).toLocaleString()}`);
  const markdown = `${lines.join("\n")}\n`;
  validateMarkdownOutput(markdown, result, args);
  return markdown;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.analysis || !args.benchmark) {
    usage();
    process.exit(args.help ? 0 : 1);
  }

  const result = computeAccountBenchmark({
    analysisReport: readJson(args.analysis),
    benchmarkReport: readJson(args.benchmark),
    analysisId: args.analysisId,
    metricKeys: args.metricKeys,
    analysisDays: args.analysisDays,
    benchmarkDays: args.benchmarkDays,
    costActiveMin: args.costActiveMin,
    objectiveField: args.objectiveField,
    objectiveType: args.objectiveType,
  });

  if (args.format === "json") {
    console.log(JSON.stringify(result, null, 2));
  } else if (args.format === "markdown") {
    process.stdout.write(renderMarkdown(result, args));
  } else {
    throw new Error(`Unsupported format: ${args.format}`);
  }
}

function isMainModule() {
  if (!process.argv[1]) return false;
  return fs.realpathSync(fileURLToPath(import.meta.url)) === fs.realpathSync(process.argv[1]);
}

if (isMainModule()) {
  main();
}
