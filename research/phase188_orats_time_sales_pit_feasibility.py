#!/usr/bin/env python3
"""Phase 188: ORATS option Time & Sales API feasibility and PIT audit.

Documentation-only. No API token, network request, purchase, vendor contact,
raw market data, alpha test, holdout, or production change is used.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from math import ceil
from pathlib import Path

HISTORY_START = date(2022, 9, 9)
AS_OF_DATE = date(2026, 11, 7)
REFERENCE_UNIVERSE = 335  # historical test universe only; not a closed universe
SESSIONS_PER_YEAR = 252
REQUESTS_PER_MINUTE = 10
TIME_SALES_ADDON_USD = 299
PLAN_CAPS = {"delayed": 20_000, "live": 100_000, "live_intraday": 1_000_000, "all_in": 1_000_000}
PLAN_TOTALS_USD = {"delayed_plus_timesales": 498, "live_plus_timesales": 598,
                   "live_intraday_plus_timesales": 898, "all_in": 899}
SOURCE_URLS = {
    "time_sales_docs": "https://orats.com/docs/time-and-sales-api",
    "data_api_pricing": "https://orats.com/data-api",
    "definitions": "https://orats.com/docs/definitions",
    "near_eod": "https://orats.com/near-eod-data",
}


def build_audit() -> dict:
    history_days = (AS_OF_DATE - HISTORY_START).days
    history_years = history_days / 365.2425
    annual_requests = REFERENCE_UNIVERSE * SESSIONS_PER_YEAR
    history_requests = int(round(annual_requests * history_years))
    request_minutes = history_requests / REQUESTS_PER_MINUTE
    request_hours = request_minutes / 60
    request_days = request_hours / 24
    quota_months = {str(cap): round(history_requests / cap, 2) for cap in PLAN_CAPS.values()}
    billing_months = {
        "delayed_plus_timesales": ceil(history_requests / PLAN_CAPS["delayed"]),
        "live_plus_timesales": ceil(history_requests / PLAN_CAPS["live"]),
        "live_intraday_plus_timesales": ceil(history_requests / PLAN_CAPS["live_intraday"]),
        "all_in": ceil(history_requests / PLAN_CAPS["all_in"]),
    }
    estimated_subscription_cost = {
        key: billing_months[key] * PLAN_TOTALS_USD[key] for key in billing_months
    }
    return {
        "phase": 188,
        "audit_as_of": AS_OF_DATE.isoformat(),
        "source": "ORATS Option Time & Sales API",
        "source_urls": SOURCE_URLS,
        "documented_history": {
            "start_date": HISTORY_START.isoformat(),
            "as_of_date": AS_OF_DATE.isoformat(),
            "calendar_days": history_days,
            "calendar_years": round(history_years, 4),
            "continuous_daily_coverage_verified": False,
            "first_live_product_availability_date_verified": False,
            "historical_first_receipt_vintages_verified": False,
            "historical_backfill_start_is_not_proof_of_live_availability": True,
        },
        "reference_universe_budget": {
            "symbols": REFERENCE_UNIVERSE,
            "status": "illustrative_reference_only_not_a_closed_universe",
            "sessions_per_year_assumption": SESSIONS_PER_YEAR,
            "requests_per_ticker_day": 1,
            "requests_per_full_universe_day": REFERENCE_UNIVERSE,
            "full_universe_sweep_minutes_at_rate_limit": round(REFERENCE_UNIVERSE / REQUESTS_PER_MINUTE, 2),
            "requests_per_year_estimate": annual_requests,
            "history_requests_estimate": history_requests,
            "history_backfill_rate_limit_hours": round(request_hours, 2),
            "history_backfill_rate_limit_days_continuous": round(request_days, 2),
            "history_quota_months_by_cap": quota_months,
            "billing_months_by_plan": billing_months,
            "estimated_subscription_cost_usd_by_plan": estimated_subscription_cost,
            "cost_assumptions": [
                "Individual public plan prices as displayed on 2026-11-07.",
                "One whole-chain request per underlying per trading day.",
                "252 sessions per year and 335 reference symbols.",
                "Excludes storage, transfer, taxes, professional licensing, retries and missing/extra symbols.",
                "Broader/open universes scale linearly; 335 is not the final universe boundary.",
            ],
        },
        "public_individual_pricing": {
            "time_sales_addon_monthly_usd": TIME_SALES_ADDON_USD,
            "delayed_data_api_monthly_usd": 199,
            "live_data_api_monthly_usd": 299,
            "live_intraday_data_api_monthly_usd": 599,
            "all_in_monthly_usd": 899,
            "monthly_request_caps": PLAN_CAPS,
            "combined_monthly_prices_usd": PLAN_TOTALS_USD,
            "free_trial_available": False,
            "institutional_license_price_verified": False,
        },
        "api_operational_limits": {
            "requests_per_minute_per_token": REQUESTS_PER_MINUTE,
            "one_ticker_or_one_contract_per_request": True,
            "json_response_row_cap": 250_000,
            "csv_response_row_cap": None,
            "large_response_redirects_to_presigned_gzip": True,
            "example_spy_full_day_rows_approx": 1_300_000,
            "example_spy_full_day_json_mb_approx": 700,
            "full_universe_live_polling_feasible_at_30_second_refresh": False,
            "live_refresh_bucket_seconds": 30,
            "live_lag_seconds_min": 10,
            "live_lag_seconds_max": 40,
        },
        "historical_live_shape": {
            "historical_session_end_et": "15:59",
            "historical_half_day_end_et": "12:59",
            "live_capture_end_et": "near 16:15",
            "historical_greeks_enrichment": ["stockPrice", "delta", "gamma", "iv", "smvValue when available"],
            "live_greeks_enrichment": [],
            "historical_greeks_source": "ORATS one-minute Greeks snapshot, not exact trade-time state",
            "live_historical_shape_parity": False,
            "same_day_expiry_greeks_warmup_null_window_et": "09:30-09:32; values resume at 09:33",
            "smv_value_null_before_field_availability": True,
            "share_class_ticker_prints_start_date": "2026-08-26",
        },
        "trade_print_semantics": {
            "one_row_per_print": True,
            "fields": ["eventTime", "eventEstTime", "eventIndex", "eventSequence", "symbol",
                       "exchangeCode", "price", "size", "bidPrice", "askPrice",
                       "exchangeSaleConditions", "aggressorSide", "spreadLeg",
                       "extendedTradingHours", "validTick", "type"],
            "aggressor_side_is_inferred": True,
            "aggressor_side_can_be_blank": True,
            "spread_leg_flag_available": True,
            "valid_tick_flag_available": True,
            "sale_conditions_available": True,
            "event_index_scope": "unique per contract, not per chain",
            "event_index_must_be_preserved_as_string": True,
            "event_sequence_step": 2,
            "cancel_shares_event_index_and_sequence_with_new": True,
            "event_key": ["symbol", "eventIndex", "type"],
            "volume_aggregation_type": "NEW",
            "cancel_rows_must_not_be_double_counted": True,
            "participant_capacity_available": False,
            "beneficial_owner_identity_available": False,
            "open_close_classification_available": False,
        },
        "source_independence": {
            "raw_source_independence_vs_ivydb_tradeflow_verified": False,
            "disposition": "Treat as a different vendor measurement of options prints, not independent raw-source replication; upstream OPRA lineage and side-inference differences remain to be verified.",
        },
        "pit_and_universe_gates": {
            "first_live_product_availability_date_verified": False,
            "first_receipt_ledger_available": False,
            "immutable_historical_vintages_verified": False,
            "continuous_daily_coverage_verified": False,
            "335_symbol_coverage_verified": False,
            "delisted_and_inactive_symbol_coverage_verified": False,
            "share_class_history_complete_before_2026_08_26": False,
            "historical_live_shape_parity": False,
            "aggressor_side_accuracy_independently_validated": False,
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
        },
        "preregistered_hypotheses": [
            "H1: net single-leg aggressor flow adds information after controlling for underlying momentum, option volume/OI, IV changes, liquidity, earnings and market regime.",
            "H2: signed flow produces temporary dealer-hedging/price-pressure effects that reverse rather than persistent informed continuation.",
            "H3: large-print and small-print signed flow have different predictive or liquidity effects; size bands must be defined ex ante.",
            "H4: spreadLeg, sale conditions, exchange and validTick explain apparent flow effects; multi-leg activity must not be double-counted.",
            "H5: signed flow combined with IV/skew changes adds information beyond either component and beyond frozen LTM/F80.",
            "H6: signed execution price versus contemporaneous NBBO/SMV measures execution urgency or trade quality, not participant identity.",
        ],
        "mandatory_controls": [
            "Keep eventIndex as a string; key by symbol, eventIndex and type.",
            "Retain NEW/CANCEL linkage; follow vendor rule to sum NEW prints only and never count cancellation rows as new volume.",
            "Preserve blank aggressorSide as unknown; do not coerce to BUY or SELL.",
            "Separate spreadLeg=true from single-leg flow; retain sale conditions and validTick.",
            "Use independent, point-in-time underlying prices; historical stockPrice/Greeks are minute-snapshot enrichments, not trade-time equity marks.",
            "Treat the 09:30-09:32 same-day-expiry Greeks warm-up as missing, not zero.",
            "Do not use the 16:00-16:15 live tail in historical backtests where backfilled days end at 15:59.",
            "Audit smvValue field availability by date and do not backfill missing values.",
            "Use chronological labels/embargo, same exposure and costs as F80, block bootstrap, issuer LOO and multiple-testing control.",
            "Separate predictive continuation from return-chasing and temporary dealer-hedging pressure.",
        ],
        "decision": "Keep as a high-priority conditional microstructure candidate for prospective capture and feasibility only. Do not treat aggressorSide as institutional identity, do not admit historical backfill as PIT, and do not start alpha tests until licensing, first-receipt, universe, side-accuracy, event/cancel and live/historical parity gates pass.",
        "controls": {
            "api_token_used": False,
            "raw_data_downloaded": False,
            "vendor_contact": False,
            "data_purchase": False,
            "holdout_used": False,
            "alpha_test_authorized": False,
            "production_changed": False,
            "f80_frozen": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase188_output/phase188_orats_time_sales_pit_audit.json"))
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": result["phase"],
        "history_start": result["documented_history"]["start_date"],
        "history_years": result["documented_history"]["calendar_years"],
        "history_requests_estimate": result["reference_universe_budget"]["history_requests_estimate"],
        "history_backfill_rate_limit_days_continuous": result["reference_universe_budget"]["history_backfill_rate_limit_days_continuous"],
        "full_universe_live_polling_feasible_at_30_second_refresh": result["api_operational_limits"]["full_universe_live_polling_feasible_at_30_second_refresh"],
        "strict_pit_admitted": result["pit_and_universe_gates"]["strict_pit_admitted"],
        "alpha_test_authorized": result["pit_and_universe_gates"]["alpha_test_authorized"],
        "f80_frozen": result["controls"]["f80_frozen"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
