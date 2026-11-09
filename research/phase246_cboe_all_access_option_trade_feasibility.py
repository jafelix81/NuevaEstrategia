#!/usr/bin/env python3
"""Phase 246: Cboe All Access option time-and-sales feasibility gate.

Documentation-only. No account, token, card authorization, API request,
vendor contact, purchase, raw data, alpha test, holdout, or production change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AUDIT_DATE = "2026-11-09"
HISTORY_START_YEAR = 2003
ORATS_HISTORY_START = "2022-09-09"
CBOE_TBT_ARCHIVE_START = "2019-10-07"
TRIAL_DAYS = 14
TRIAL_POINTS_PER_DAY = 500
HISTORICAL_POINTS_PER_REQUEST = 15
MAX_ROWS_PER_PAGE = 10_000

BUY_SIDE_PRICE_CLASSES = {"Above Ask", "On Ask"}
SELL_SIDE_PRICE_CLASSES = {"Below Bid", "On Bid"}
UNKNOWN_PRICE_CLASSES = {"Mid Market", "Crossed Market", "No Market"}


def classify_trade_at(value: str) -> str:
    """Conservative price-location proxy, never participant identity."""
    label = str(value or "").strip()
    if label in BUY_SIDE_PRICE_CLASSES:
        return "BUY_SIDE_PRICE_CLASS"
    if label in SELL_SIDE_PRICE_CLASSES:
        return "SELL_SIDE_PRICE_CLASS"
    if label in UNKNOWN_PRICE_CLASSES or not label:
        return "UNKNOWN"
    return "UNKNOWN"


def count_as_new_trade(cancel_flag: int | str) -> bool:
    """Only documented normal prints are eligible for initial volume."""
    try:
        return int(cancel_flag) == 0
    except (TypeError, ValueError):
        return False


def build_audit() -> dict:
    requests_per_day = TRIAL_POINTS_PER_DAY // HISTORICAL_POINTS_PER_REQUEST
    total_full_requests = requests_per_day * TRIAL_DAYS
    return {
        "phase": 246,
        "audit_date": AUDIT_DATE,
        "status": "HIGH_PRIORITY_CONDITIONAL_HISTORICAL_TRADE_MEASUREMENT_CANDIDATE_NO_PIT_NO_ALPHA",
        "source": "Cboe DataShop / LiveVol All Access API option time-and-sales",
        "advertised_history_start_year": HISTORY_START_YEAR,
        "comparators": {
            "orats_time_sales_history_start": ORATS_HISTORY_START,
            "cboe_tbt_archive_history_start": CBOE_TBT_ARCHIVE_START,
        },
        "documented_api": {
            "historical_option_trades": True,
            "historical_option_trades_with_greeks": True,
            "historical_start_claim": "2003",
            "historical_request_points": HISTORICAL_POINTS_PER_REQUEST,
            "max_rows_per_page": MAX_ROWS_PER_PAGE,
            "sequence_pagination": True,
            "trade_fields": [
                "security", "root", "expiry", "strike", "option_type",
                "option_trade_price", "option_trade_size", "option_trade_at",
                "exchange_id", "condition_id", "exchange_seq_no", "seq_no",
                "timestamp", "cancel_flag",
            ],
            "greek_fields": ["iv", "delta", "gamma", "vega", "theta", "rho",
                             "dollar_delta", "dollar_vega", "dollar_theta"],
            "trade_at_values": sorted(BUY_SIDE_PRICE_CLASSES | SELL_SIDE_PRICE_CLASSES | UNKNOWN_PRICE_CLASSES),
            "cancel_flag_values": {
                "0": "normal",
                "1": "canceled_trade",
                "2": "cancel_trade_message",
            },
            "time_filter_timezone_documentation": "Eastern Standard Time",
        },
        "trade_at_measurement": {
            "buy_side_price_class_proxy": sorted(BUY_SIDE_PRICE_CLASSES),
            "sell_side_price_class_proxy": sorted(SELL_SIDE_PRICE_CLASSES),
            "unknown_or_ambiguous": sorted(UNKNOWN_PRICE_CLASSES),
            "is_aggressor_identity": False,
            "is_participant_identity": False,
            "is_open_close_classification": False,
        },
        "trial": {
            "days": TRIAL_DAYS,
            "points_per_day": TRIAL_POINTS_PER_DAY,
            "historical_points_per_request": HISTORICAL_POINTS_PER_REQUEST,
            "max_full_historical_requests_per_day": requests_per_day,
            "max_full_historical_requests_over_trial": total_full_requests,
            "card_authorization_required": True,
            "published_trial_charge_usd": 0,
            "trial_overage_available": False,
            "trial_sip_access": False,
            "historical_opra_price_field_access_during_trial": "UNVERIFIED",
        },
        "published_paid_tiers": {
            "tier3": {"points_per_month": 1_250_000, "monthly_usd": 2499},
            "tier4": {"points_per_month": 4_000_000, "monthly_usd": 4599},
        },
        "pit_and_coverage_gates": {
            "advertised_history_is_first_live_availability": False,
            "first_receipt_ledger": False,
            "immutable_correction_vintages": False,
            "venue_coverage_verified": False,
            "historical_completeness_verified": False,
            "inactive_delisted_coverage_verified": False,
            "adjusted_contract_identity_verified": False,
            "timezone_dst_semantics_verified": False,
            "trade_at_accuracy_verified": False,
            "historical_trial_field_access_verified": False,
            "source_independence_vs_orats_opra_lineage_verified": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
        },
        "initial_trial_sample_design": {
            "historical_eras": ["2003-2006", "2011-2014", "2018-2021", "2024-2026"],
            "symbol_strata": [
                "liquid_index_or_etf", "large_cap", "mid_cap",
                "lower_liquidity", "inactive_or_delisted",
                "adjusted_contract_or_corporate_action",
            ],
            "target_ticker_date_pairs": 24,
            "budget_points_before_pagination": 24 * HISTORICAL_POINTS_PER_REQUEST,
            "pagination_and_high_volume_headroom": "remaining daily points are reserved for additional pages and failures",
            "sample_is_not_universe_coverage": True,
        },
        "decision": (
            "Elevate to a high-priority conditional sample-acquisition candidate only. "
            "Historical backfill is not PIT; no trade flow is admitted until trial access, "
            "venue coverage, cancellation linkage, NBBO/time semantics, identity, licensing "
            "and prospective receipt controls are verified."
        ),
        "controls": {
            "account_signup": False,
            "card_authorization": False,
            "api_token_used": False,
            "api_requests_sent": 0,
            "raw_data_downloaded": False,
            "vendor_contact": False,
            "data_purchase": False,
            "return_test": False,
            "alpha_test_authorized": False,
            "bootstrap_loo": False,
            "oos_test": False,
            "holdout_used": False,
            "universe_changed": False,
            "production_changed": False,
            "f80_frozen": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("phase246_output/phase246_cboe_all_access_option_trade_feasibility.json"))
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": result["phase"],
        "history_start_year": result["advertised_history_start_year"],
        "trial_requests_per_day": result["trial"]["max_full_historical_requests_per_day"],
        "trial_requests_total": result["trial"]["max_full_historical_requests_over_trial"],
        "trial_historical_price_access": result["trial"]["historical_opra_price_field_access_during_trial"],
        "strict_pit_admitted": result["pit_and_coverage_gates"]["strict_pit_admitted"],
        "alpha_test_authorized": result["pit_and_coverage_gates"]["alpha_test_authorized"],
        "f80_frozen": result["controls"]["f80_frozen"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
