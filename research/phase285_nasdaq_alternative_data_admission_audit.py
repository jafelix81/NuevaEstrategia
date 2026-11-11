"""Deterministic metadata-only admission contract for Nasdaq FIS SLD and UREF."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_result() -> dict[str, Any]:
    return {
        "phase": 285,
        "audit_date_utc": "2026-11-11",
        "overall_status": "METADATA_FEASIBILITY_ONLY_NO_DATA_ADMISSION_NO_ALPHA",
        "controls": {
            "raw_data_downloaded": False,
            "api_key_used": False,
            "vendor_contacted": False,
            "trial_started": False,
            "license_or_terms_accepted": False,
            "pit_admission": False,
            "alpha_admission": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
        },
        "fis_astec_sld": {
            "product": "FIS Astec Analytics Securities Lending Data",
            "access": "premium",
            "history_start_by_table": {
                "FIS/POS": "2013-07-01",
                "FIS/U1": "2013-07-01",
                "FIS/U2": "2014-01-01",
                "FIS/R1": "2012-01-02",
            },
            "delivery": {
                "schedule_utc": "12:30 weekdays",
                "content": "previous trading day",
                "actual_first_receipt_captured": False,
                "immutable_historical_vintages_established": False,
            },
            "coverage": {
                "advertised_securities": "45000+",
                "asset_scope": ["equities", "fixed_income"],
                "advertised_countries": "110+",
                "equity_only_count_known": False,
                "f80_universe_overlap_measured": False,
                "active_and_inactive_advertised": True,
                "inactive_retention_verified": False,
            },
            "identity": {
                "primary_vendor_identifier": "AstecID",
                "astec_id_format": "6- or 8-digit integer",
                "isin_cusip_trading_symbol_nullable": True,
                "effective_dated_crosswalk_verified": False,
            },
            "semantics": {
                "retail_loan_rate_definition": "prime broker loans to clients, e.g. hedge funds",
                "retail_loan_rate_is_not_retail_investor_rate": True,
                "borrower_or_fund_identity_available": False,
                "loan_is_proof_of_short_sale": False,
                "loan_stage_A": "outstanding",
                "loan_stage_N": "new",
                "loan_stage_R": "recalled_or_returned_not_distinguishable",
                "u1_uses_same_lending_program_scope_for_loans_and_availability": True,
                "reconstruct_u1_from_pos_units_divided_by_u2_available_units": False,
                "r1_excludes_term_trades": True,
                "r1_new_units_are_subset_of_r1_units": True,
            },
            "pit_admitted": False,
            "alpha_admitted": False,
            "decision": "CONDITIONAL_PRIORITY_1_SAMPLE_GATE_ONLY",
        },
        "nasdaq_urefint": {
            "product": "Intraday US Retail Equities Flow",
            "access": "premium",
            "history_start": "2016-01-04",
            "coverage": {
                "advertised_instruments": "10000+ US stocks, ADRs and ETPs",
                "price_below_usd_1_excluded": True,
                "point_in_time_ticker_symbology_claimed": True,
                "f80_universe_overlap_measured": False,
            },
            "tables": {
                "current": {"code": "UREF/FFI", "start": "2025-01-02"},
                "historical": [
                    "UREF/FFIH16", "UREF/FFIH17", "UREF/FFIH18",
                    "UREF/FFIH19", "UREF/FFIH20", "UREF/FFIH21",
                    "UREF/FFIH22", "UREF/FFIH23", "UREF/FFIH24",
                ],
            },
            "frequency": "15-minute",
            "delivery": {
                "schedule_utc": "13:30-20:00",
                "lag": "less than 30 minutes after interval end",
                "actual_first_receipt_captured": False,
                "immutable_historical_vintages_established": False,
                "dst_and_early_close_reconciliation_done": False,
            },
            "fields": {
                "update_time_populated_from": "2022-06-01",
                "update_time_semantics": "record generation time in Eastern Time, not documented first receipt",
                "is_healthy_populated_from": "2021-08-02",
                "is_healthy_scope": "overall retail dollar-volume health for the interval, shared across tickers",
                "known_incomplete_dates_before_2021": True,
                "affected_date_ticker_list_applied": False,
            },
            "identity": {
                "row_key": ["date", "minute", "ticker"],
                "permanent_security_identifier_in_documented_schema": False,
                "effective_dated_security_crosswalk_verified": False,
            },
            "research_role": "retail-flow control_or_interaction_not_institutional_identity",
            "pit_admitted": False,
            "alpha_admitted": False,
            "decision": "CONDITIONAL_PRIORITY_2_CONTROL_SAMPLE_GATE_ONLY",
        },
        "nasdaq_uref_daily_separate_product": {
            "product": "US Retail Equities Flow",
            "tables": {
                "daily": "UREF/DF",
                "intraday_30_minute": "UREF/IF",
            },
            "history_start": "2016-01",
            "delivery": "10:00 UTC Tuesday-Saturday with previous trading day data",
            "includes_pre_and_post_market_in_daily_table": True,
            "same_as_urefint_15_minute_product": False,
            "pit_admitted": False,
        },
        "hypotheses": [
            "FIS borrow-demand, utilization and borrow-cost changes may predict downside continuation or squeeze risk; sign unspecified.",
            "UREF retail net flow may help control for retail participation when testing FIS incremental information.",
            "FIS and UREF divergence may contain incremental information, subject to separate source-quality and OOS gates.",
        ],
        "required_next_gates": [
            "authorized existing entitlement or explicit sample/license permission",
            "raw bytes, extraction receipt timestamps, source metadata and SHA-256",
            "FIS AstecID continuity, optional identifier coverage and effective-dated security crosswalk",
            "FIS POS/U1/U2/R1 denominator and row-grain reconciliation",
            "UREF affected-date list, ticker history, DST and early-close reconciliation",
            "F80 universe overlap and inactive/delisted coverage measurement",
            "fresh prospective holdout and preregistered chronological OOS protocol",
        ],
    }


def validate_result(result: dict[str, Any]) -> None:
    assert result["phase"] == 285
    controls = result["controls"]
    for key in (
        "raw_data_downloaded", "api_key_used", "vendor_contacted",
        "trial_started", "license_or_terms_accepted", "pit_admission",
        "alpha_admission", "holdout_used", "production_changed",
        "universe_changed", "capital_changed", "parameters_changed",
    ):
        assert controls[key] is False, key
    assert controls["f80_frozen"] is True

    fis = result["fis_astec_sld"]
    assert fis["history_start_by_table"]["FIS/R1"] < fis["history_start_by_table"]["FIS/POS"]
    assert fis["coverage"]["equity_only_count_known"] is False
    assert fis["identity"]["isin_cusip_trading_symbol_nullable"] is True
    assert fis["semantics"]["retail_loan_rate_is_not_retail_investor_rate"] is True
    assert fis["semantics"]["borrower_or_fund_identity_available"] is False
    assert fis["semantics"]["loan_is_proof_of_short_sale"] is False
    assert fis["semantics"]["reconstruct_u1_from_pos_units_divided_by_u2_available_units"] is False
    assert fis["semantics"]["r1_excludes_term_trades"] is True
    assert fis["pit_admitted"] is False and fis["alpha_admitted"] is False

    uref = result["nasdaq_urefint"]
    assert uref["history_start"] == "2016-01-04"
    assert uref["fields"]["update_time_populated_from"] == "2022-06-01"
    assert uref["fields"]["is_healthy_populated_from"] == "2021-08-02"
    assert uref["fields"]["known_incomplete_dates_before_2021"] is True
    assert uref["delivery"]["actual_first_receipt_captured"] is False
    assert uref["pit_admitted"] is False and uref["alpha_admitted"] is False

    daily = result["nasdaq_uref_daily_separate_product"]
    assert daily["same_as_urefint_15_minute_product"] is False
    assert daily["pit_admitted"] is False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    validate_result(result)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
