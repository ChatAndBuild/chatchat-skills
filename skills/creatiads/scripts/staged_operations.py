#!/usr/bin/env python3
"""Staged operation plan builders for TikTok MCP-first creatiads operations.

Every plan includes:
- source reads (what to read before acting)
- target IDs
- payload summary
- MCP tool/API route
- default disabled/paused state
- risks
- required approval
- post-write readback plan

Create, update, status, delete, share, upload operations are approval-gated.
Activation requires separate approval from creation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class StagedPlan:
    operation: str
    capability: str
    api_path: str | None = None
    source_reads: list[dict[str, Any]] = field(default_factory=list)
    target_ids: dict[str, Any] = field(default_factory=dict)
    payload_summary: dict[str, Any] = field(default_factory=dict)
    mcp_tool: str | None = ""
    default_state: str = "paused_or_disabled"
    risks: list[str] = field(default_factory=list)
    approval_required: bool = True
    post_write_readback: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_campaign_create(advertiser_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return StagedPlan(
        operation="campaign_create",
        capability="campaign_create",
        api_path="/campaign/create/",
        source_reads=[{"tool": "campaign_get", "purpose": "Verify no duplicate campaign name."}],
        target_ids={"advertiser_id": advertiser_id},
        payload_summary={k: v for k, v in payload.items() if k != "access_token"},
        mcp_tool="campaign_create",
        risks=["Duplicate campaign name may be rejected.", "Budget or objective_type mismatch may cause delivery failure."],
    ).to_dict()


def plan_campaign_update(advertiser_id: str, campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return StagedPlan(
        operation="campaign_update",
        capability="campaign_update",
        api_path="/campaign/update/",
        source_reads=[{"tool": "campaign_get", "filtering": {"campaign_ids": [campaign_id]}, "purpose": "Read current campaign state before update."}],
        target_ids={"advertiser_id": advertiser_id, "campaign_id": campaign_id},
        payload_summary={k: v for k, v in payload.items() if k != "access_token"},
        mcp_tool="campaign_update",
        risks=["Updating budget or objective_type mid-flight may reset learning phase."],
    ).to_dict()


def plan_campaign_status(advertiser_id: str, campaign_ids: list[str], target_status: str) -> dict[str, Any]:
    return StagedPlan(
        operation="campaign_status_update",
        capability="campaign_status",
        api_path="/campaign/status/update/",
        source_reads=[{"tool": "campaign_get", "filtering": {"campaign_ids": campaign_ids}, "purpose": "Verify current status before toggling."}],
        target_ids={"advertiser_id": advertiser_id, "campaign_ids": campaign_ids},
        payload_summary={"status": target_status},
        mcp_tool="campaign_status_update",
        risks=["Enabling a paused campaign may cause uncontrolled spend.", "Disabling an active campaign may impact ongoing delivery pacing."],
    ).to_dict()


def plan_adgroup_create(advertiser_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return StagedPlan(
        operation="adgroup_create",
        capability="adgroup_create",
        api_path="/adgroup/create/",
        source_reads=[{"tool": "campaign_get", "purpose": "Verify parent campaign exists and is active."}],
        target_ids={"advertiser_id": advertiser_id, "campaign_id": payload.get("campaign_id", "")},
        payload_summary={k: v for k, v in payload.items() if k != "access_token"},
        mcp_tool="adgroup_create",
        risks=["Bid or budget too low may limit delivery.", "Placement/targeting too narrow may not spend."],
    ).to_dict()


def plan_adgroup_budget(advertiser_id: str, adgroup_ids: list[str], budget: float, budget_mode: str = "daily") -> dict[str, Any]:
    return StagedPlan(
        operation="adgroup_budget_update",
        capability="adgroup_budget",
        api_path="/adgroup/budget/update/",
        source_reads=[{"tool": "adgroup_get", "filtering": {"adgroup_ids": adgroup_ids}, "purpose": "Verify current budget before updating."}],
        target_ids={"advertiser_id": advertiser_id, "adgroup_ids": adgroup_ids},
        payload_summary={"budget": budget, "budget_mode": budget_mode},
        mcp_tool="adgroup_budget_update",
        risks=["Large budget change may reset delivery learning.", "Minimum budget thresholds vary by billing event."],
    ).to_dict()


def plan_ad_create(advertiser_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return StagedPlan(
        operation="ad_create",
        capability="ad_create",
        api_path="/ad/create/",
        source_reads=[{"tool": "adgroup_get", "purpose": "Verify parent adgroup exists."}],
        target_ids={"advertiser_id": advertiser_id, "adgroup_id": payload.get("adgroup_id", "")},
        payload_summary={k: v for k, v in payload.items() if k != "access_token"},
        mcp_tool="ad_create",
        risks=["Creative may be rejected in review.", "Identity/page binding must match the ad creative."],
    ).to_dict()


def plan_media_upload(advertiser_id: str, media_type: str, file_path: str) -> dict[str, Any]:
    tool = None
    return StagedPlan(
        operation=f"{media_type}_upload",
        capability=f"{media_type}_upload",
        api_path=f"/file/{media_type}/ad/upload/",
        source_reads=[],
        target_ids={"advertiser_id": advertiser_id},
        payload_summary={"file": file_path, "media_type": media_type},
        mcp_tool=tool,
        risks=[
            f"{media_type.title()} may be too large or in an unsupported format.",
            "The v2 TikTok MCP mapping has no new_name for media upload endpoints yet.",
        ],
    ).to_dict()


def plan_asset_delete(advertiser_id: str, asset_ids: list[str]) -> dict[str, Any]:
    return StagedPlan(
        operation="asset_delete",
        capability="asset_delete",
        api_path="/creative_asset/delete/",
        source_reads=[{"tool": "file_video_ad_info_get", "purpose": "Verify assets exist before deletion."}],
        target_ids={"advertiser_id": advertiser_id, "asset_ids": asset_ids},
        payload_summary={"asset_count": len(asset_ids)},
        mcp_tool="creative_asset_delete",
        risks=["Deletion is irreversible.", "Assets in use by active ads cannot be deleted."],
    ).to_dict()


def plan_asset_share(advertiser_id: str, asset_ids: list[str], target_advertiser_ids: list[str]) -> dict[str, Any]:
    return StagedPlan(
        operation="asset_share",
        capability="asset_share",
        api_path="/creative_asset/share/",
        source_reads=[{"tool": "file_video_ad_info_get", "purpose": "Verify assets exist and are shareable."}],
        target_ids={"advertiser_id": advertiser_id, "target_advertiser_ids": target_advertiser_ids},
        payload_summary={"asset_count": len(asset_ids), "target_count": len(target_advertiser_ids)},
        mcp_tool="creative_asset_share_get",
        risks=["Shared assets remain visible to target advertisers.", "Asset ownership metadata may transfer."],
    ).to_dict()


# ── Copy/rebuild strategy builders ─────────────────────────────────

def plan_campaign_copy(
    advertiser_id: str,
    source_campaign_id: str,
    *,
    new_name: str | None = None,
    smart_plus: bool = False,
) -> dict[str, Any]:
    """Plan a campaign copy: read source → build payload → stage for approval."""
    capability = "smart_plus_campaign_create" if smart_plus else "campaign_create"
    tool = "campaign_create"
    return StagedPlan(
        operation=f"campaign_copy_{'smart_plus' if smart_plus else 'regular'}",
        capability=capability,
        source_reads=[
            {"tool": "campaign_get", "filtering": {"campaign_ids": [source_campaign_id]}, "purpose": "Read source campaign to build copy payload."},
        ],
        target_ids={"advertiser_id": advertiser_id, "source_campaign_id": source_campaign_id},
        payload_summary={"new_name": new_name or f"Copy of {source_campaign_id}", "source_campaign_id": source_campaign_id, "smart_plus": smart_plus},
        mcp_tool=tool,
        default_state="paused_or_disabled",
        risks=["Copy may inherit budget/bid settings that need adjustment.", "Smart+ copy may require app onboarding if objective_type is APP_PROMOTION."],
    ).to_dict()


def plan_adgroup_copy(
    advertiser_id: str,
    source_adgroup_id: str,
    target_campaign_id: str,
    *,
    new_name: str | None = None,
) -> dict[str, Any]:
    return StagedPlan(
        operation="adgroup_copy",
        capability="adgroup_create",
        source_reads=[
            {"tool": "adgroup_get", "filtering": {"adgroup_ids": [source_adgroup_id]}, "purpose": "Read source adgroup to build copy payload."},
            {"tool": "campaign_get", "filtering": {"campaign_ids": [target_campaign_id]}, "purpose": "Verify target campaign exists."},
        ],
        target_ids={"advertiser_id": advertiser_id, "source_adgroup_id": source_adgroup_id, "target_campaign_id": target_campaign_id},
        payload_summary={"new_name": new_name or f"Copy of {source_adgroup_id}", "target_campaign_id": target_campaign_id},
        mcp_tool="adgroup_create",
        default_state="paused_or_disabled",
        risks=["Adgroup copy within a different campaign may inherit incompatible placement/targeting settings."],
    ).to_dict()


def plan_ad_copy(
    advertiser_id: str,
    source_ad_id: str,
    target_adgroup_id: str,
    *,
    new_name: str | None = None,
) -> dict[str, Any]:
    return StagedPlan(
        operation="ad_copy",
        capability="ad_create",
        source_reads=[
            {"tool": "ad_get", "filtering": {"ad_ids": [source_ad_id]}, "purpose": "Read source ad to build copy payload."},
            {"tool": "adgroup_get", "filtering": {"adgroup_ids": [target_adgroup_id]}, "purpose": "Verify target adgroup exists."},
        ],
        target_ids={"advertiser_id": advertiser_id, "source_ad_id": source_ad_id, "target_adgroup_id": target_adgroup_id},
        payload_summary={"new_name": new_name or f"Copy of {source_ad_id}", "target_adgroup_id": target_adgroup_id},
        mcp_tool="ad_create",
        default_state="paused_or_disabled",
        risks=["Creative material may need re-upload if not shared to target advertiser.", "Identity binding must match the target adgroup/promoted object."],
    ).to_dict()


# ── Portfolio match-campaign and export builders ────────────────────

def plan_portfolio_match_campaign(
    advertiser_id: str,
    portfolio_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    return StagedPlan(
        operation="portfolio_match_campaign",
        capability="portfolio_get",
        source_reads=[
            {"tool": "creative_portfolio_get", "payload": {"portfolio_id": portfolio_id}, "purpose": "Read portfolio creative assets."},
            {"tool": "campaign_get", "filtering": {"campaign_ids": [campaign_id]}, "purpose": "Verify target campaign and its objective/creative requirements."},
        ],
        target_ids={"advertiser_id": advertiser_id, "portfolio_id": portfolio_id, "campaign_id": campaign_id},
        payload_summary={"portfolio_id": portfolio_id, "campaign_id": campaign_id},
        mcp_tool="creative_portfolio_get",
        risks=["Portfolio assets may not match campaign creative format requirements.", "Portfolio may contain assets not owned by this advertiser."],
    ).to_dict()


def plan_portfolio_export(
    advertiser_id: str,
    portfolio_id: str,
    *,
    export_format: str = "json",
) -> dict[str, Any]:
    return StagedPlan(
        operation="portfolio_export",
        capability="portfolio_get",
        source_reads=[
            {"tool": "creative_portfolio_get", "payload": {"portfolio_id": portfolio_id}, "purpose": "Read full portfolio creative assets for export."},
        ],
        target_ids={"advertiser_id": advertiser_id, "portfolio_id": portfolio_id},
        payload_summary={"export_format": export_format},
        mcp_tool="creative_portfolio_get",
        risks=["Portfolio export may expose creative asset metadata.", "Export size may be large for portfolios with many assets."],
        post_write_readback=["Verify exported file is complete and valid JSON."],
    ).to_dict()


# ── Payload normalization helpers ─────────────────────────────────

def normalize_smartplus_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Smart+ campaign create payload with sensible defaults."""
    normalized = dict(payload)
    if "objective_type" in normalized and normalized["objective_type"] == "APP_PROMOTION":
        normalized.setdefault("campaign_app_profile_page_state", "OFF")
    normalized.setdefault("budget_mode", "daily")
    normalized.setdefault("operation_status", "DISABLE")
    return normalized


def normalize_adgroup_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize adgroup create payload with safe defaults."""
    normalized = dict(payload)
    normalized.setdefault("operation_status", "DISABLE")
    if "budget" in normalized:
        normalized.setdefault("budget_mode", "daily")
    return normalized


def normalize_ad_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize ad create payload — default to disabled."""
    normalized = dict(payload)
    normalized.setdefault("operation_status", "DISABLE")
    return normalized


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Creatiads staged operation plan builders.")
    parser.add_argument("command", choices=["campaign-create", "campaign-update", "campaign-status", "adgroup-create", "adgroup-budget", "ad-create", "media-upload", "asset-delete", "asset-share"])
    parser.add_argument("--advertiser-id", default="")
    parser.add_argument("--campaign-id", default="")
    parser.add_argument("--campaign-ids", default="")
    parser.add_argument("--adgroup-ids", default="")
    parser.add_argument("--asset-ids", default="")
    parser.add_argument("--target-advertiser-ids", default="")
    parser.add_argument("--target-status", default="ENABLE")
    parser.add_argument("--budget", type=float)
    parser.add_argument("--budget-mode", default="daily")
    parser.add_argument("--media-type", choices=["image", "video"], default="video")
    parser.add_argument("--file-path", default="")
    parser.add_argument("--input", help="JSON file with payload")
    parser.add_argument("--out", help="Output file")
    args = parser.parse_args()

    payload = {}
    if args.input:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))

    result: dict[str, Any] = {}
    cmd = args.command
    if cmd == "campaign-create":
        result = plan_campaign_create(args.advertiser_id, payload)
    elif cmd == "campaign-update":
        result = plan_campaign_update(args.advertiser_id, args.campaign_id, payload)
    elif cmd == "campaign-status":
        result = plan_campaign_status(args.advertiser_id, [i.strip() for i in args.campaign_ids.split(",") if i.strip()], args.target_status)
    elif cmd == "adgroup-create":
        result = plan_adgroup_create(args.advertiser_id, payload)
    elif cmd == "adgroup-budget":
        result = plan_adgroup_budget(args.advertiser_id, [i.strip() for i in args.adgroup_ids.split(",") if i.strip()], args.budget or 0, args.budget_mode)
    elif cmd == "ad-create":
        result = plan_ad_create(args.advertiser_id, payload)
    elif cmd == "media-upload":
        result = plan_media_upload(args.advertiser_id, args.media_type, args.file_path)
    elif cmd == "asset-delete":
        result = plan_asset_delete(args.advertiser_id, [i.strip() for i in args.asset_ids.split(",") if i.strip()])
    elif cmd == "asset-share":
        result = plan_asset_share(args.advertiser_id, [i.strip() for i in args.asset_ids.split(",") if i.strip()], [i.strip() for i in args.target_advertiser_ids.split(",") if i.strip()])

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
