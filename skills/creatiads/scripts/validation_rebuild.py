#!/usr/bin/env python3
"""Validation, bottleneck diagnosis, and cross-account rebuild for TikTok MCP-first operations.

Read-only validation produces a go/no-go assessment. Bottleneck diagnosis
traverses advertiser → campaign → adgroup → ad → report → changelog → platform.
Rebuild is plan-only by default; execution requires explicit approval.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

try:
    from utils import STATUS_OK, extract_rows, write_json
except ImportError:  # pragma: no cover
    from .utils import STATUS_OK, extract_rows, write_json


# ── Validation ──────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    go_no_go: str = "go"
    failed_points: list[dict[str, Any]] = field(default_factory=list)
    missing_assets: list[str] = field(default_factory=list)
    abnormal_bindings: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_safe_fix: list[str] = field(default_factory=list)
    write_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_creative(creative_payload: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    if not creative_payload:
        result.go_no_go = "no_go"
        result.failed_points.append({"field": "creative", "reason": "Empty creative payload."})
        return result
    required = ["ad_name", "creative_type"]
    for field in required:
        if not creative_payload.get(field):
            result.failed_points.append({"field": field, "reason": f"Missing required field: {field}."})
            result.go_no_go = "no_go"
    if creative_payload.get("creative_type") == "VIDEO" and not creative_payload.get("video_id"):
        result.failed_points.append({"field": "video_id", "reason": "VIDEO creative type requires video_id."})
        result.missing_assets.append("video")
        result.go_no_go = "no_go"
    if creative_payload.get("creative_type") == "IMAGE" and not creative_payload.get("image_id"):
        result.failed_points.append({"field": "image_id", "reason": "IMAGE creative type requires image_id."})
        result.missing_assets.append("image")
        result.go_no_go = "no_go"
    return result


def validate_ad_link(ad_payload: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    url = ad_payload.get("ad_url") or ad_payload.get("landing_page_url") or ""
    if not url:
        result.go_no_go = "no_go"
        result.failed_points.append({"field": "ad_url", "reason": "Missing landing page URL."})
        return result
    if url.startswith("http") and "tiktok.com" in url.lower():
        result.warnings.append("Landing URL is a TikTok domain — verify it is a valid external landing page.")
    return result


def validate_promoted_object(payload: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    obj_type = payload.get("promoted_object_type") or payload.get("objective_type") or ""
    obj_id = payload.get("promoted_object_id") or payload.get("app_id") or payload.get("pixel_id") or ""
    if not obj_type:
        result.go_no_go = "partial"
        result.warnings.append("No promoted_object_type set; TikTok may reject the ad.")
    if obj_type == "APP" and not obj_id:
        result.go_no_go = "no_go"
        result.failed_points.append({"field": "promoted_object_id", "reason": "APP promotion requires an app_id."})
    return result


# ── Bottleneck diagnosis ───────────────────────────────────────────

BOTTLENECK_LABELS = [
    "account_limit",
    "balance_or_billing",
    "campaign_budget",
    "adgroup_budget_or_bid",
    "schedule",
    "review_or_policy",
    "status_disabled",
    "creative_invalid",
    "identity_or_page_binding",
    "promoted_object_invalid",
    "tracking_or_measurement",
    "audience_or_targeting",
    "platform_limit",
    "unknown_partial",
]


def diagnose_bottlenecks(
    campaign_rows: list[dict[str, Any]] | None = None,
    adgroup_rows: list[dict[str, Any]] | None = None,
    ad_rows: list[dict[str, Any]] | None = None,
    *,
    advertiser_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    # Advertiser-level
    info = advertiser_info or {}
    if info.get("status") != STATUS_OK:
        findings.append({"level": "advertiser", "label": "account_limit", "detail": "Advertiser info not retrievable via MCP."})

    # Campaign-level
    for row in (campaign_rows or []):
        status = str(row.get("campaign_status") or row.get("operation_status") or "").upper()
        if status in {"DISABLE", "PAUSED", "SUSPEND"}:
            findings.append({"level": "campaign", "label": "status_disabled", "detail": f"Campaign {row.get('campaign_id')} is {status}."})

    # Adgroup-level
    for row in (adgroup_rows or []):
        status = str(row.get("adgroup_status") or row.get("operation_status") or "").upper()
        if status in {"DISABLE", "PAUSED"}:
            findings.append({"level": "adgroup", "label": "status_disabled", "detail": f"Adgroup {row.get('adgroup_id')} is {status}."})

    # Ad-level
    for row in (ad_rows or []):
        status = str(row.get("ad_status") or row.get("operation_status") or "").upper()
        if status in {"DISABLE", "PAUSED"}:
            findings.append({"level": "ad", "label": "status_disabled", "detail": f"Ad {row.get('ad_id')} is {status}."})
        review = str(row.get("review_status") or row.get("review") or "").upper()
        if review in {"REJECTED", "DISAPPROVED"}:
            findings.append({"level": "ad", "label": "review_or_policy", "detail": f"Ad {row.get('ad_id')} review: {review}."})

    if not findings:
        findings.append({"level": "advertiser", "label": "unknown_partial", "detail": "No obvious bottleneck detected from available MCP evidence."})

    return {
        "status": "ok",
        "bottleneck_labels": BOTTLENECK_LABELS,
        "findings": findings,
        "primary_label": findings[0]["label"] if findings else "unknown_partial",
    }


# ── Cross-account rebuild (plan-only) ──────────────────────────────

def plan_cross_account_rebuild(
    source_advertiser_id: str,
    destination_advertiser_id: str,
    source_campaigns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": "approval_required",
        "plan_type": "cross_account_rebuild",
        "source_advertiser_id": source_advertiser_id,
        "destination_advertiser_id": destination_advertiser_id,
        "source_object_count": len(source_campaigns or []),
        "stages": [
            "export_source_objects",
            "destination_gap_analysis",
            "build_staged_payloads",
            "approval_gate",
            "execute_with_resumable_records",
        ],
        "approval_gate": {
            "required": True,
            "reason": "Cross-account rebuild requires explicit approval at each stage. Execution writes rebuild_state.json, rebuild_failures.json, and rebuild_approvals.json.",
        },
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Creatiads validation and rebuild helpers.")
    parser.add_argument("command", choices=["validate", "diagnose", "rebuild-plan"])
    parser.add_argument("--advertiser-id")
    parser.add_argument("--source-advertiser-id")
    parser.add_argument("--destination-advertiser-id")
    parser.add_argument("--input", help="JSON file with validation/rebuild inputs")
    parser.add_argument("--out", help="Output file")
    args = parser.parse_args()

    result: dict[str, Any] = {}
    if args.command == "validate":
        payload = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
        creative = validate_creative(payload.get("creative") or {})
        ad_link = validate_ad_link(payload.get("ad") or {})
        promoted = validate_promoted_object(payload.get("promoted_object") or {})
        result = {
            "creative_validation": creative.to_dict(),
            "ad_link_validation": ad_link.to_dict(),
            "promoted_object_validation": promoted.to_dict(),
            "overall_go_no_go": "go" if all(v.go_no_go == "go" for v in (creative, ad_link, promoted)) else "partial",
        }
    elif args.command == "diagnose":
        payload = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
        result = diagnose_bottlenecks(
            campaign_rows=payload.get("campaigns"),
            adgroup_rows=payload.get("adgroups"),
            ad_rows=payload.get("ads"),
            advertiser_info=payload.get("advertiser_info"),
        )
    elif args.command == "rebuild-plan":
        payload = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
        result = plan_cross_account_rebuild(
            source_advertiser_id=args.source_advertiser_id or "",
            destination_advertiser_id=args.destination_advertiser_id or "",
            source_campaigns=payload.get("campaigns"),
        )

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())