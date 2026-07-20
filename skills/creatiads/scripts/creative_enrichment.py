#!/usr/bin/env python3
"""Creative preview and retention enrichment for TikTok MCP-first reports.

Resolves preview evidence from MCP sources and builds retention/fatigue scoring.
One row in creative_previews.json per final report ad row.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from utils import SECRET_RE, STATUS_OK, STATUS_PARTIAL, extract_rows, write_json
except ImportError:  # pragma: no cover
    from .utils import SECRET_RE, STATUS_OK, STATUS_PARTIAL, extract_rows, write_json


# Only these statuses count as "concrete preview coverage".
COVERAGE_STATUSES = {"inline_image", "action_url_only", "spark_post_url"}

PREVIEW_EVIDENCE_FIELDS = (
    "preview_image_url", "preview_action_url", "thumbnail_url", "cover_url",
    "video_cover_url", "poster_url", "image_url", "video_url", "playable_url",
    "preview_url", "permalink_url", "spark_post_url", "image_link",
    "main_image_url", "cover_image_url", "product_image_url", "sku_image_url",
    "additional_image_urls", "video_poster_url", "download_url",
    "ad_url", "ad_url_list", "landing_page_url", "landing_page_urls",
)

RESULT_OBJECTIVE_TOKENS = {
    "ENGAGEMENT", "TRAFFIC", "REACH", "VIDEO_VIEW", "LEAD_GENERATION",
    "CONVERSATION", "CLICK", "MESSAGING", "FOLLOWERS",
}

IMAGE_ID_FIELDS = {"image_id", "image_ids", "image_material_id", "web_uri"}
VIDEO_ID_FIELDS = {"video_id", "video_ids", "video_material_id"}
SPARK_ID_FIELDS = {"item_id", "item_ids", "tiktok_item_id", "spark_post_id", "anchor_id"}
CATALOG_ID_FIELDS = {"catalog_id", "catalog_ids"}
PRODUCT_ID_FIELDS = {"product_id", "product_ids", "item_group_id", "item_group_ids", "sku_id", "sku_ids"}
PRODUCT_SET_ID_FIELDS = {"product_set_id", "product_set_ids", "set_id"}
DETAIL_ID_FIELDS = {"ad_id", "ad_ids", "ad_id_v2", "smart_plus_ad_id", "ad_material_id", "material_id"}


def _dimension(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None and isinstance(row.get("dimensions"), dict):
        value = row["dimensions"].get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    return str(value or "")


def _metric(row: dict[str, Any], key: str) -> float:
    value = row.get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    try:
        return float(str(value or 0).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def _objective(row: dict[str, Any]) -> str:
    return _dimension(row, "objective_type").upper()


def _primary_result(row: dict[str, Any]) -> tuple[float, str, float | None, str]:
    """Return the decision metric without relabeling result as conversion."""
    conversion = _metric(row, "conversion")
    result = _metric(row, "result")
    spend = _metric(row, "spend")
    objective = _objective(row)
    use_result = bool(result and not conversion and any(token in objective for token in RESULT_OBJECTIVE_TOKENS))
    if use_result:
        cost = _metric(row, "cost_per_result") or (spend / result if result else 0)
        return result, "result", cost if cost else None, "cost_per_result"
    cost = _metric(row, "cost_per_conversion") or (spend / conversion if conversion else 0)
    return conversion, "conversion", cost if cost else None, "cost_per_conversion"


def _collect_values(payload: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys:
                if isinstance(value, list):
                    found.extend(str(item) for item in value if item)
                elif value:
                    found.append(str(value))
            found.extend(_collect_values(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_collect_values(item, keys))
    return sorted(set(found))


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            result.append(v)
    return result


def _contains_id(payload: Any, target: str, keys: set[str]) -> bool:
    if not target:
        return False
    return target in set(_collect_values(payload, keys))


def _media_lookup(media_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in media_rows:
        for ref in _collect_values(row, IMAGE_ID_FIELDS | VIDEO_ID_FIELDS | {"material_id"}):
            lookup.setdefault(ref, row)
    return lookup


def _rows_by_refs(rows: list[dict[str, Any]], refs: list[str], keys: set[str]) -> list[dict[str, Any]]:
    if not refs:
        return []
    ref_set = set(refs)
    matched: list[dict[str, Any]] = []
    for row in rows:
        values = set(_collect_values(row, keys))
        if values & ref_set:
            matched.append(row)
    return matched


def _catalog_rows_for_details(detail_rows: list[dict[str, Any]], catalog_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    product_refs = _unique(_collect_values(detail_rows, PRODUCT_ID_FIELDS))
    product_set_refs = _unique(_collect_values(detail_rows, PRODUCT_SET_ID_FIELDS))
    catalog_refs = _unique(_collect_values(detail_rows, CATALOG_ID_FIELDS))
    matched = [
        *_rows_by_refs(catalog_rows, product_refs, PRODUCT_ID_FIELDS),
        *_rows_by_refs(catalog_rows, product_set_refs, PRODUCT_SET_ID_FIELDS),
        *_rows_by_refs(catalog_rows, catalog_refs, CATALOG_ID_FIELDS),
    ]
    return _unique_dicts(matched)


def _unique_dicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        key = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _looks_like_url(value: str) -> bool:
    text = str(value or "").strip()
    if not text or text in {"-", "0", "None", "null", "<redacted>"}:
        return False
    return text.startswith(("http://", "https://"))


def _first_url(payloads: list[Any], fields: tuple[str, ...]) -> str:
    for payload in payloads:
        for value in _collect_values(payload, set(fields)):
            text = str(value or "").strip()
            if _looks_like_url(text):
                return text
    return ""


def _safe_inline_image_url(value: str) -> str:
    """Skip signed media URLs that source sanitization would redact."""
    if not value or value == "<redacted>" or SECRET_RE.search(value):
        return ""
    return value


def _details_for_ad(ad_id: str, detail_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in detail_rows if _contains_id(row, ad_id, DETAIL_ID_FIELDS)]


def _resolve_preview(
    detail_rows: list[dict[str, Any]],
    media_by_ref: dict[str, dict[str, Any]],
    *,
    spark_rows: list[dict[str, Any]] | None = None,
    catalog_rows: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    image_refs = _unique(_collect_values(detail_rows, IMAGE_ID_FIELDS))
    video_refs = _unique(_collect_values(detail_rows, VIDEO_ID_FIELDS))
    spark_refs = _unique(_collect_values(detail_rows, SPARK_ID_FIELDS))
    product_refs = _unique(_collect_values(detail_rows, PRODUCT_ID_FIELDS))
    product_set_refs = _unique(_collect_values(detail_rows, PRODUCT_SET_ID_FIELDS))

    image_media = [media_by_ref[ref] for ref in image_refs if ref in media_by_ref]
    video_media = [media_by_ref[ref] for ref in video_refs if ref in media_by_ref]
    media_rows = [*image_media, *video_media]
    spark_media = _rows_by_refs(spark_rows or [], spark_refs, SPARK_ID_FIELDS | {"id", "video_id"})
    catalog_media = _catalog_rows_for_details(detail_rows, catalog_rows or [])

    preview_image = _safe_inline_image_url(
        _first_url(detail_rows, ("preview_image_url", "thumbnail_url", "cover_url", "video_cover_url", "poster_url", "image_url"))
        or _first_url(media_rows, ("image_url", "thumbnail_url", "cover_url", "video_cover_url", "poster_url"))
        or _first_url(spark_media, ("image_url", "thumbnail_url", "cover_url", "video_cover_url", "poster_url", "video_poster_url", "image_link"))
        or _first_url(catalog_media, ("image_url", "image_link", "main_image_url", "product_image_url", "sku_image_url", "thumbnail_url", "cover_image_url", "cover_url"))
    )
    preview_action = (
        _first_url(detail_rows, (
            "preview_action_url", "video_url", "playable_url", "preview_url",
            "permalink_url", "spark_post_url", "ad_url", "ad_url_list",
            "landing_page_url", "landing_page_urls", "download_url",
        ))
        or _first_url(media_rows, ("video_url", "playable_url", "preview_url", "permalink_url", "spark_post_url"))
        or _first_url(spark_media, ("preview_url", "video_url", "playable_url", "permalink_url", "spark_post_url", "download_url"))
        or _first_url(catalog_media, ("preview_url", "video_url", "playable_url", "permalink_url", "product_url"))
    )
    spark_url = _first_url([*detail_rows, *media_rows, *spark_media], ("spark_post_url", "permalink_url"))

    asset_refs = _unique([*image_refs, *video_refs])
    catalog_refs = _unique([*product_refs, *product_set_refs])
    if preview_image:
        status = "inline_image"
    elif spark_url:
        status = "spark_post_url"
        preview_action = preview_action or spark_url
    elif preview_action:
        status = "action_url_only"
    elif asset_refs:
        status = "asset_reference"
    elif spark_refs:
        status = "spark_post_reference"
    elif catalog_refs:
        status = "catalog_reference"
    else:
        status = "unavailable"

    return {
        "preview_status": status,
        "preview_image_url": preview_image,
        "preview_action_url": preview_action,
        "asset_reference": "" if (preview_image or preview_action) else ",".join(asset_refs or spark_refs[:4]),
        "spark_post_reference": "" if (preview_image or preview_action or asset_refs) else ",".join(spark_refs[:4]),
        "catalog_reference": "" if (preview_image or preview_action or asset_refs or spark_refs) else ",".join(catalog_refs[:4]),
    }


def build_creative_previews(
    final_ad_rows: list[dict[str, Any]],
    smart_details: list[dict[str, Any]],
    *,
    ad_details_rows: list[dict[str, Any]] | None = None,
    media_rows: list[dict[str, Any]] | None = None,
    spark_rows: list[dict[str, Any]] | None = None,
    catalog_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ad_details = ad_details_rows or []
    media = media_rows or []
    media_by_ref = _media_lookup(media)

    preview_rows: list[dict[str, Any]] = []
    for row in final_ad_rows:
        ad_id = _dimension(row, "ad_id")
        matching_details = [
            row,
            *_details_for_ad(ad_id, ad_details),
            *_details_for_ad(ad_id, smart_details),
            *_details_for_ad(ad_id, media),
        ]
        resolved = _resolve_preview(
            matching_details,
            media_by_ref,
            spark_rows=spark_rows,
            catalog_rows=catalog_rows,
        )
        preview_rows.append({
            "ad_id": ad_id,
            "ad_name": _dimension(row, "ad_name"),
            "spend": _metric(row, "spend"),
            **resolved,
        })

    with_preview = sum(1 for r in preview_rows if r["preview_status"] in COVERAGE_STATUSES)
    status = STATUS_OK if with_preview else STATUS_PARTIAL if preview_rows else "supported_empty"
    return {
        "status": status,
        "rows": preview_rows,
        "coverage": {"total": len(preview_rows), "with_preview": with_preview},
        "calls": {
            "ad_details": "ok" if ad_details_rows else "supported_empty",
            "media": "ok" if media_rows else "supported_empty",
            "spark_posts": "ok" if spark_rows else "supported_empty",
            "catalog": "ok" if catalog_rows else "supported_empty",
        },
    }


def build_creative_retention(ad_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in ad_rows:
        plays = _metric(row, "video_play_actions")
        p25 = _metric(row, "video_views_p25")
        p50 = _metric(row, "video_views_p50")
        p75 = _metric(row, "video_views_p75")
        p100 = _metric(row, "video_views_p100")
        watched_2s = _metric(row, "video_watched_2s")
        watched_6s = _metric(row, "video_watched_6s")
        engaged = _metric(row, "engaged_view")
        spend = _metric(row, "spend")
        conversion = _metric(row, "conversion")
        result = _metric(row, "result")
        primary_value, primary_label, primary_cost, primary_cost_label = _primary_result(row)
        value = max(_metric(row, "total_purchase_value"), _metric(row, "onsite_total_purchase_value"))
        ad_id = _dimension(row, "ad_id")
        ad_name = _dimension(row, "ad_name")
        rows.append({
            "ad_id": ad_id,
            "ad_name": ad_name,
            "spend": spend,
            "conversion": conversion,
            "result": result,
            "primary_result": primary_value,
            "primary_metric_label": primary_label,
            "primary_cost": primary_cost,
            "primary_cost_label": primary_cost_label,
            "cost_per_conversion": _metric(row, "cost_per_conversion") or (spend / conversion if conversion else None),
            "cost_per_result": _metric(row, "cost_per_result") or (spend / result if result else None),
            "value": value,
            "plays": plays,
            "hook_rate": p25 / plays if plays else None,
            "mid_retention": p50 / p25 if p25 else None,
            "deep_retention": p75 / p50 if p50 else None,
            "completion_rate": p100 / plays if plays else None,
            "conversion_from_play": conversion / plays if plays else None,
            "primary_result_from_play": primary_value / plays if plays else None,
            "cost_per_retained_viewer": spend / watched_6s if watched_6s else None,
            "engaged_view": engaged,
            "watched_2s": watched_2s,
            "watched_6s": watched_6s,
            "p25": p25, "p50": p50, "p75": p75, "p100": p100,
            "roas": value / spend if spend else None,
        })

    sorted_by_result = sorted(rows, key=lambda r: (r.get("primary_result") or 0, r.get("conversion") or 0, r.get("hook_rate") or 0), reverse=True)
    sorted_by_spend = sorted(rows, key=lambda r: (r.get("spend") or 0, -(r.get("primary_result") or 0)), reverse=True)
    winners = sorted_by_result[:10]
    fatigue_candidates = sorted_by_spend[:10]
    high_spend_low_conv = [r for r in sorted_by_spend[:15] if (r.get("spend") or 0) > 0 and (r.get("conversion") or 0) < 1]
    high_click_low_retention = [r for r in rows if r.get("mid_retention") and r["mid_retention"] < 0.3 and (r.get("spend") or 0) > 0]

    return {
        "status": STATUS_OK if rows else "supported_empty",
        "rows": rows,
        "winners": winners,
        "fatigue_candidates": fatigue_candidates,
        "high_spend_low_conversion": high_spend_low_conv,
        "high_click_low_retention": high_click_low_retention,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Creative preview and retention enrichment.")
    parser.add_argument("--ad-rows", help="JSON file with final report ad rows")
    parser.add_argument("--smart-details", help="JSON file with Smart+ detail rows")
    parser.add_argument("--ad-details-rows", help="JSON file with pre-fetched ad detail rows (from ad_get)")
    parser.add_argument("--media-rows", help="JSON file with pre-fetched media rows (from image/video/spark info)")
    parser.add_argument("--spark-rows", help="JSON file with pre-fetched Spark post rows")
    parser.add_argument("--catalog-rows", help="JSON file with pre-fetched catalog product/set rows")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--retention-only", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    def _load(path: str) -> list[dict[str, Any]]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("rows") or data if isinstance(data, list) else []

    ad_rows = []
    if args.ad_rows:
        ad_rows = _load(args.ad_rows)

    smart_details = []
    if args.smart_details:
        smart_details = _load(args.smart_details)

    if args.retention_only:
        result = build_creative_retention(ad_rows)
    elif args.preview_only:
        ad_details_rows = _load(args.ad_details_rows) if args.ad_details_rows else None
        media_rows = _load(args.media_rows) if args.media_rows else None
        spark_rows = _load(args.spark_rows) if args.spark_rows else None
        catalog_rows = _load(args.catalog_rows) if args.catalog_rows else None
        result = build_creative_previews(ad_rows, smart_details, ad_details_rows=ad_details_rows, media_rows=media_rows, spark_rows=spark_rows, catalog_rows=catalog_rows)
    else:
        ad_details_rows = _load(args.ad_details_rows) if args.ad_details_rows else None
        media_rows = _load(args.media_rows) if args.media_rows else None
        spark_rows = _load(args.spark_rows) if args.spark_rows else None
        catalog_rows = _load(args.catalog_rows) if args.catalog_rows else None
        retention = build_creative_retention(ad_rows)
        previews = build_creative_previews(ad_rows, smart_details, ad_details_rows=ad_details_rows, media_rows=media_rows, spark_rows=spark_rows, catalog_rows=catalog_rows)
        result = {"retention": retention, "previews": previews}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
