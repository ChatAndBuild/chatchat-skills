#!/usr/bin/env python3
"""Build concrete TikTok MCP preview calls from a Creatiads run directory.

The planner keeps placeholders in mcp_tasks.jsonl so a plan stays stable across
runs. Subexecutors use this helper after dependencies exist to convert those
placeholders into exact read-only MCP calls for final-ad preview enrichment.
The script never calls MCP.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from creative_enrichment import (
        CATALOG_ID_FIELDS,
        IMAGE_ID_FIELDS,
        PRODUCT_ID_FIELDS,
        PRODUCT_SET_ID_FIELDS,
        SPARK_ID_FIELDS,
        VIDEO_ID_FIELDS,
        _collect_values,
    )
    from run_report import select_top_ids
    from utils import chunked, extract_rows
except ImportError:  # pragma: no cover
    from .creative_enrichment import (
        CATALOG_ID_FIELDS,
        IMAGE_ID_FIELDS,
        PRODUCT_ID_FIELDS,
        PRODUCT_SET_ID_FIELDS,
        SPARK_ID_FIELDS,
        VIDEO_ID_FIELDS,
        _collect_values,
    )
    from .run_report import select_top_ids
    from .utils import chunked, extract_rows


IMAGE_BATCH_SIZE = 100
VIDEO_BATCH_SIZE = 60
SPARK_PAGE_SIZE = 50


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _source_rows(run_dir: Path, source_id: str) -> list[dict[str, Any]]:
    payload = _load_json(run_dir / "sources" / f"{source_id}.json")
    rows = extract_rows(payload)
    return rows if rows else []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _detail_rows(run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(_source_rows(run_dir, "ad_details_for_enrichment"))
    rows.extend(_source_rows(run_dir, "ad_structure"))
    rows.extend(_source_rows(run_dir, "smart_plus_ads"))
    return rows


def _catalog_groups(rows: list[dict[str, Any]], default_bc_id: str = "") -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, set[str]]] = {}
    for row in rows:
        bc_ids = _collect_values(row, {"catalog_authorized_bc_id", "identity_authorized_bc_id", "bc_id"})
        catalog_ids = _collect_values(row, CATALOG_ID_FIELDS)
        product_ids = _collect_values(row, PRODUCT_ID_FIELDS)
        set_ids = _collect_values(row, PRODUCT_SET_ID_FIELDS)
        for catalog_id in catalog_ids:
            bc_id = (bc_ids[0] if bc_ids else default_bc_id).strip()
            if not bc_id or not catalog_id:
                continue
            item = grouped.setdefault((bc_id, catalog_id), {"product_ids": set(), "product_set_ids": set()})
            item["product_ids"].update(pid for pid in product_ids if pid)
            item["product_set_ids"].update(pid for pid in set_ids if pid)
    calls: list[dict[str, Any]] = []
    for (bc_id, catalog_id), values in sorted(grouped.items()):
        calls.append({
            "bc_id": bc_id,
            "catalog_id": catalog_id,
            "product_ids": sorted(values["product_ids"]),
            "product_set_ids": sorted(values["product_set_ids"]),
        })
    return calls


def build_preview_mcp_calls(
    *,
    run_dir: Path,
    advertiser_id: str,
    top_limit: int = 60,
    bc_id: str = "",
    spark_pages: int = 2,
) -> dict[str, Any]:
    current_rows = _source_rows(run_dir, "current_ads")
    detail_rows = _detail_rows(run_dir)
    top_ad_ids = select_top_ids(current_rows, "ad_id", limit=top_limit)

    image_ids = _unique(_collect_values(detail_rows, IMAGE_ID_FIELDS))
    video_ids = _unique(_collect_values(detail_rows, VIDEO_ID_FIELDS))
    spark_ids = _unique(_collect_values(detail_rows, SPARK_ID_FIELDS))
    catalog_groups = _catalog_groups(detail_rows, bc_id)

    calls: dict[str, list[dict[str, Any]]] = {
        "ad_details_for_enrichment": [],
        "creative_preview_images": [],
        "creative_preview_videos": [],
        "creative_preview_spark_posts": [],
        "creative_preview_catalog_products": [],
        "creative_preview_catalog_sets": [],
    }
    if top_ad_ids:
        calls["ad_details_for_enrichment"].append({
            "tool": "ad_get",
            "params": {
                "advertiser_id": advertiser_id,
                "filtering": {"ad_ids": top_ad_ids},
                "page": 1,
                "page_size": min(max(len(top_ad_ids), 1), top_limit),
            },
        })
    for batch in chunked(image_ids, IMAGE_BATCH_SIZE):
        calls["creative_preview_images"].append({
            "tool": "file_image_ad_info_get",
            "params": {"advertiser_id": advertiser_id, "image_ids": batch},
            "retry": "If TikTok returns permission errors for a mixed batch, split into smaller batches or single IDs and keep all successful rows.",
        })
    for batch in chunked(video_ids, VIDEO_BATCH_SIZE):
        calls["creative_preview_videos"].append({
            "tool": "file_video_ad_info_get",
            "params": {"advertiser_id": advertiser_id, "video_ids": batch},
            "retry": "If a mixed batch fails, split into smaller batches or single IDs and keep all successful rows.",
        })
    if len(spark_ids) > 1:
        for page in range(1, max(spark_pages, 1) + 1):
            calls["creative_preview_spark_posts"].append({
                "tool": "tt_video_list_get",
                "params": {
                    "advertiser_id": advertiser_id,
                    "item_types": ["VIDEO", "CAROUSEL"],
                    "page": page,
                    "page_size": SPARK_PAGE_SIZE,
                },
                "match_item_ids": spark_ids,
            })
    for item_id in spark_ids:
        calls["creative_preview_spark_posts"].append({
            "tool": "tt_video_list_get",
            "params": {
                "advertiser_id": advertiser_id,
                "keyword": item_id,
                "item_types": ["VIDEO", "CAROUSEL"],
                "page": 1,
                "page_size": 1,
            },
            "match_item_ids": [item_id],
        })
    for group in catalog_groups:
        for batch in chunked(group["product_ids"], 100):
            calls["creative_preview_catalog_products"].append({
                "tool": "catalog_product_get",
                "params": {
                    "bc_id": group["bc_id"],
                    "catalog_id": group["catalog_id"],
                    "product_ids": batch,
                    "page": 1,
                    "page_size": 100,
                },
            })
        for product_set_id in group["product_set_ids"]:
            calls["creative_preview_catalog_sets"].append({
                "tool": "catalog_set_get",
                "params": {
                    "bc_id": group["bc_id"],
                    "catalog_id": group["catalog_id"],
                    "product_set_id": product_set_id,
                    "return_product_count": False,
                },
            })

    return {
        "run_dir": str(run_dir),
        "advertiser_id": advertiser_id,
        "top_ad_count": len(top_ad_ids),
        "image_id_count": len(image_ids),
        "video_id_count": len(video_ids),
        "spark_item_id_count": len(spark_ids),
        "catalog_group_count": len(catalog_groups),
        "calls": calls,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare concrete preview MCP calls.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--advertiser-id", required=True)
    parser.add_argument("--top-limit", type=int, default=60)
    parser.add_argument("--bc-id", default="")
    parser.add_argument("--spark-pages", type=int, default=2)
    parser.add_argument("--source-id", choices=[
        "ad_details_for_enrichment",
        "creative_preview_images",
        "creative_preview_videos",
        "creative_preview_spark_posts",
        "creative_preview_catalog_products",
        "creative_preview_catalog_sets",
    ])
    args = parser.parse_args()

    result = build_preview_mcp_calls(
        run_dir=args.run_dir,
        advertiser_id=args.advertiser_id,
        top_limit=args.top_limit,
        bc_id=args.bc_id,
        spark_pages=args.spark_pages,
    )
    if args.source_id:
        result = {**result, "calls": {args.source_id: result["calls"].get(args.source_id, [])}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
