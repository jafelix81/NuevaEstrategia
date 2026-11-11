#!/usr/bin/env python3
"""Phase 236: Cboe Trade-by-Trade (TBT) source feasibility and strict-PIT gate.

This is a documentation-backed, fail-closed admission audit. It does not
download licensed Cboe data, infer beneficial owners, or test returns.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PHASE = 236
DOCUMENTED_LIVE_FLOOR = date(2026, 2, 20)  # first public Cboe launch notice located
ARCHIVE_START = date(2019, 10, 7)
SOURCE_URLS = {
    "cboe_product": "https://datashop.cboe.com/enhanced-us-options-trade-by-trade-execution-detail",
    "cboe_spec_v1_1": "https://datashop.cboe.com/documents/TBT_Spec_v1.1.pdf",
    "cboe_launch_2026_02_20": "https://cdn.cboe.com/resources/trader_news/2026/Cboe-Traders-Weekly-for-Friday-February-20-2026.pdf",
    "cboe_launch_2026_03_06": "https://cdn.cboe.com/resources/trader_news/2026/Cboe-Traders-Weekly-for-Friday-March-6-2026.pdf",
    "sec_rule_filing_2025_088": "https://www.sec.gov/files/rules/sro/cboe/2025/34-104415.pdf",
    "cboe_fee_schedule_2026_04_21": "https://cdn.cboe.com/resources/membership/Cboe_FeeSchedule.pdf",
    "cboe_open_close": "https://datashop.cboe.com/cboe-options-open-close-volume-summary",
    "cboe_c2_tbt_notice_2026_11_06": "https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-c2-2026-029",
}

REQUIRED_FIELDS = {
    "TRANSACT_TIME", "TRADING_DT", "UNDERLYING", "OSI_ROOT", "EXPIRE_DATE",
    "CALL_PUT_FLAG", "STRIKE_PRICE", "SIZE", "PRICE", "NBBO_BID", "NBBO_ASK",
    "BBO_BID", "BBO_ASK", "SIDE", "OPEN_CLOSE", "CAPACITY", "TRADE_TYPE",
    "EXEC_ID", "COMPLEX_EXEC_ID", "SESSION", "TRADING_SEGMENT",
}
CAPACITY_VALUES = {"MarketMaker", "Customer", "ProCustomer", "BrokerDealer", "Firm"}
SIDE_VALUES = {"B", "S"}
OPEN_CLOSE_VALUES = {"O", "C"}
PROVISIONAL_TRADE_TYPE = "Provisional"

def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None

def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)

def classify_trade_date(trade_date: str, live_floor: str = DOCUMENTED_LIVE_FLOOR.isoformat()) -> str:
    trade = _parse_date(trade_date)
    floor = _parse_date(live_floor)
    if trade is None or floor is None:
        return "UNKNOWN_INVALID_DATE"
    if trade < floor:
        return "RETROSPECTIVE_BACKFILL_NOT_STRICT_PIT"
    return "LIVE_PRODUCT_WINDOW_RECEIPT_REQUIRED"

def strict_pit_gate(
    *,
    trade_date: str,
    first_receipt_utc: str | None,
    raw_sha256: str | None,
    vintage_id: str | None,
    schema_version: str | None,
    security_identity_resolved: bool,
    internal_license_confirmed: bool,
    event_name: str = "schedule",
) -> dict[str, Any]:
    """Admit only a version received prospectively for a live-product trade date."""
    status = classify_trade_date(trade_date)
    reasons: list[str] = []
    trade = _parse_date(trade_date)
    receipt = _parse_timestamp(first_receipt_utc)
    if status == "UNKNOWN_INVALID_DATE":
        reasons.append("INVALID_TRADE_DATE")
    elif status == "RETROSPECTIVE_BACKFILL_NOT_STRICT_PIT":
        reasons.append("TRADE_DATE_PRECEDES_DOCUMENTED_LIVE_PRODUCT_FLOOR")
    if event_name != "schedule":
        reasons.append("NON_SCHEDULED_RECEIPT_NOT_PIT")
    if receipt is None:
        reasons.append("FIRST_RECEIPT_TIMESTAMP_MISSING_OR_NAIVE")
    elif trade is not None and receipt.date() <= trade:
        reasons.append("T_PLUS_ONE_RECEIPT_NOT_AFTER_TRADE_DATE")
    if not raw_sha256 or not re.fullmatch(r"[0-9a-fA-F]{64}", raw_sha256):
        reasons.append("RAW_SHA256_MISSING_OR_INVALID")
    if not vintage_id:
        reasons.append("IMMUTABLE_VINTAGE_ID_MISSING")
    if not schema_version:
        reasons.append("SCHEMA_VERSION_MISSING")
    if not security_identity_resolved:
        reasons.append("EFFECTIVE_DATED_SECURITY_IDENTITY_UNRESOLVED")
    if not internal_license_confirmed:
        reasons.append("INTERNAL_USE_LICENSE_NOT_CONFIRMED")
    return {
        "eligible": len(reasons) == 0,
        "status": "STRICT_PIT_DATA_GATE_PASS" if not reasons else "STRICT_PIT_NOT_ADMITTED",
        "reasons": reasons,
        "trade_date": trade.isoformat() if trade else None,
        "first_receipt_utc": receipt.isoformat().replace("+00:00", "Z") if receipt else None,
        "knowledge_time_is_pipeline_receipt": True,
        "earliest_execution_rule": (
            "Use the first actual regular-session open strictly after the recorded first receipt; "
            "under the project's end-of-day discipline, do not execute before that session's close."
        ),
    }

def validate_row_semantics(row: dict[str, Any]) -> dict[str, Any]:
    """Validate only documented categorical invariants; do not infer aggressor or owner."""
    errors = []
    if row.get("SIDE") not in SIDE_VALUES:
        errors.append("SIDE_NOT_B_OR_S")
    if row.get("OPEN_CLOSE") not in OPEN_CLOSE_VALUES:
        errors.append("OPEN_CLOSE_NOT_O_OR_C")
    if row.get("CAPACITY") not in CAPACITY_VALUES:
        errors.append("CAPACITY_UNKNOWN")
    try:
        size = float(row.get("SIZE"))
        if size <= 0:
            errors.append("SIZE_NOT_POSITIVE")
    except (TypeError, ValueError):
        errors.append("SIZE_INVALID")
    for field in ("TRANSACT_TIME", "TRADING_DT", "UNDERLYING", "OSI_ROOT", "TRADE_TYPE"):
        if row.get(field) in (None, ""):
            errors.append(f"{field}_MISSING")
    provisional = row.get("TRADE_TYPE") == PROVISIONAL_TRADE_TYPE
    return {
        "valid_documented_fields": not errors,
        "errors": errors,
        "provisional_trade_type": provisional,
        "trade_type_requires_separate_bucket": provisional,
        "aggressor_side_inferred": False,
        "beneficial_owner_identified": False,
    }

def build_audit() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "date": "2026-11-09",
        "status": "CBOE_TBT_HIGH_VALUE_C1_EXECUTION_MEASUREMENT_CANDIDATE_NOT_PIT_ADMITTED",
        "source": {
            "product": "Enhanced US Options Trade-by-Trade Execution Detail",
            "venue_scope": ["C1"],
            "planned_venues": ["C2", "BZX", "EDGX"],
            "archive_start_claim": ARCHIVE_START.isoformat(),
            "first_public_launch_documentation_floor": DOCUMENTED_LIVE_FLOOR.isoformat(),
            "archive_before_live_floor": "RETROSPECTIVE_BACKFILL_NOT_STRICT_PIT",
            "delivery": "T+1 overnight after midnight ET; typical 00:30-01:30 ET",
            "actual_first_receipt_logs_available": False,
            "correction_vintages_verified": False,
            "historical_inactive_underlying_coverage_verified": False,
            "representative_raw_sample_audited": False,
            "licensing_confirmed": False,
        },
        "documented_fields": {
            "trade_and_contract": ["TRANSACT_TIME", "TRADING_DT", "FLOOR_ACTION_TS", "UNDERLYING",
                                   "OSI_ROOT", "EXPIRE_DATE", "CALL_PUT_FLAG", "STRIKE_PRICE",
                                   "SIZE", "PRICE"],
            "market_context": ["NBBO_BID", "NBBO_ASK", "BBO_BID", "BBO_ASK"],
            "trade_classification": ["SIDE", "OPEN_CLOSE", "CAPACITY", "TRADE_TYPE", "SESSION",
                                     "TRADING_SEGMENT"],
            "linkage": ["EXEC_ID", "COMPLEX_EXEC_ID"],
            "capacity_values": sorted(CAPACITY_VALUES),
            "side_values": sorted(SIDE_VALUES),
            "open_close_values": sorted(OPEN_CLOSE_VALUES),
            "trade_type_special_handling": [
                "QCC, compression, routed, auction, floor, complex and provisional types must be "
                "separately classified or quarantined under a preregistered rule."
            ],
        },
        "measurement_advantage_vs_option_sentiment": [
            "TBT exposes side, open/close, capacity, trade type and contract size at trade level.",
            "These fields can be crossed directly after raw-row reconstruction; Option Sentiment's 80-field "
            "daily aggregate does not expose the same directional cross-tabs.",
            "Execution IDs provide a potential route to pair/complex-leg reconciliation, subject to sample validation."
        ],
        "non_inferences": [
            "CAPACITY is an exchange clearing-origin category, not beneficial-owner identity or proof of informed trading.",
            "SIDE B/S is documented as Buy/Sell; do not call it aggressor direction without an explicit rule/sample validation.",
            "OPEN_CLOSE is not open interest and does not identify a unique beneficial owner's net position.",
            "C1-only activity is not all-OPRA or whole-market options flow.",
            "Execution IDs may link sides/legs; do not sum rows as independent trades until row cardinality is empirically established."
        ],
        "pit_protocol": {
            "live_floor_basis": "Cboe's 2026-02-20 Traders Weekly states the TBT dataset was launched; this is the first located public launch documentation, not a verified first subscriber receipt.",
            "archive_start_is_not_live_start": True,
            "receipt_rule": "Preserve each file version, first receipt UTC, raw SHA-256, trade date, schema version and correction parent; use only after actual receipt.",
            "t_plus_one": "File is for the prior trade date and typically delivered after midnight ET; use TRADING_DT, not calendar date of TRANSACT_TIME around GTH midnight.",
            "execution_rule": "First actual regular-session open strictly after first receipt; EOD strategy execution no earlier than that session close.",
            "manual_or_backfilled_files": "Never strict PIT.",
        },
        "commercial": {
            "subscription_fee_usd_per_month": 12000,
            "historical_ad_hoc_fee_usd_per_month": 8000,
            "free_trial": "Up to one month may be available to eligible users who have not previously received the product/trial; not requested.",
            "external_redistribution": "Prohibited by current product page; internal-use license and derived-data rights require review.",
            "purchase_or_vendor_contact_made": False,
        },
        "admission": {
            "data_feasibility": "CONDITIONAL_HIGH_PRIORITY_C1_ONLY",
            "strict_historical_pit": False,
            "strict_prospective_pit": False,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
        "next_gates": [
            "Obtain a lawful representative sample or eligible free trial; do not purchase without approval.",
            "Measure row grain: one execution versus buy/sell-side rows; reconcile EXEC_ID and COMPLEX_EXEC_ID.",
            "Validate side semantics, capacity mapping, open/close, trade-type coverage, NBBO/BBO and late floor timestamps.",
            "Quantify C1 share of total OPRA volume and historical underlying/date coverage, including inactive names.",
            "Obtain actual first-receipt logs and append-only corrections; archive backfill remains retrospective.",
            "Confirm internal-use and derived-feature licensing, fee schedule and data retention terms.",
            "Only then preregister one C1-specific signed/opening-flow hypothesis with prior-return, liquidity, IV and event controls."
        ],
        "source_urls": SOURCE_URLS,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="phase236_cboe_tbt_feasibility_result.json")
    args = parser.parse_args()
    result = build_audit()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": PHASE,
        "status": result["status"],
        "archive_start": result["source"]["archive_start_claim"],
        "live_documentation_floor": result["source"]["first_public_launch_documentation_floor"],
        "venue_scope": result["source"]["venue_scope"],
        "strict_pit_admitted": result["admission"]["strict_historical_pit"],
        "output": str(path),
    }, indent=2))

if __name__ == "__main__":
    main()
