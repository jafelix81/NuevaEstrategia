"""Deterministic metadata-only feasibility contract for Nasdaq NOTO and NOP."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_result() -> dict[str, Any]:
    return {
        "phase": 286,
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
        "noto": {
            "product": "Nasdaq Options Trade Outline",
            "venue": "NOM",
            "access": "premium_internal_use_subject_to_license",
            "history_start": "2011-11",
            "market_scope": "all option series traded on NOM; no other-exchange intraday trades",
            "market_share_context": "approximately 5-6 percent in Q2 2024 per SEC filing; not current coverage proof",
            "eod": {
                "availability": "next business day, approximately 07:00 ET in SEC-filed product description",
                "includes_total_industry_volume": True,
                "includes_open_interest": True,
                "includes_origin_open_close_quantity_and_volume": True,
                "actual_first_receipt_captured": False,
            },
            "intraday": {
                "frequency": "10-minute",
                "availability": "within 2 minutes after each interval per SEC-filed product description",
                "snapshots_are_cumulative": True,
                "current_table_resets_utc": "01:40",
                "historical_table_update_utc": "21:00",
                "actual_first_receipt_captured": False,
                "correction_and_bust_vintages_verified": False,
            },
            "origin_types": ["Customer", "Broker-Dealer", "Market Maker", "Firm", "Professional"],
            "professional_definition": "not broker/dealer; more than 390 listed-options orders per day on average during a calendar month for own beneficial accounts",
            "professional_is_institutional_identity": False,
            "named_beneficial_owner_available": False,
            "opening_closing_semantics": {
                "opening_buy": "creates or increases a long option position",
                "opening_write": "creates or increases a short option position",
                "closing_buy": "reduces or eliminates a short option position",
                "closing_sale": "reduces or eliminates a long option position",
                "is_aggressor_side": False,
            },
            "contract_identity": {
                "series_fields": ["underlying_symbol", "option_symbol", "expiration_date", "strike_price", "product_kind", "series_type"],
                "effective_dated_option_master_verified": False,
            },
            "fees_usd": {
                "eod_monthly": 575,
                "intraday_monthly": 2000,
                "history_36m_eod_for_current_distributor": 3000,
                "history_36m_intraday_for_current_distributor": 6000,
                "external_derived_data_monthly": 4000,
                "ad_hoc_historical_price_conflict": {
                    "current_rulebook_eod_per_requested_month": 575,
                    "current_rulebook_intraday_per_requested_month": 2000,
                    "official_price_list_eod_per_requested_month": 250,
                    "official_price_list_intraday_per_requested_month": 500,
                    "resolved": False,
                },
            },
            "historical_vintages_established": False,
            "pit_admitted": False,
            "alpha_admitted": False,
            "decision": "CONDITIONAL_PRIORITY_1_EOD_SAMPLE_GATE_ONLY",
        },
        "nasdaq_options_trade_outline_family": {
            "advertised_venues": ["NOM", "PHLX", "ISE", "GEMX", "MRX", "NTX"],
            "all_venues_have_identical_schema_and_history": False,
            "combined_panel_admitted": False,
        },
        "nasdaq_options_pulse": {
            "product": "Nasdaq Options Pulse",
            "history_start": "2019-01",
            "frequency": "10-minute",
            "granularity": ["symbol", "sector_industry", "market"],
            "documented_inputs": "customer and professional-customer opening-buy transactions across Nasdaq options exchanges",
            "schema_is_derived_sentiment_score": True,
            "formula_and_version_history_verified": False,
            "independent_of_noto": False,
            "pit_admitted": False,
            "alpha_admitted": False,
            "decision": "CONDITIONAL_PRIORITY_4_DERIVED_COMPARATOR_ONLY",
        },
        "hypotheses": [
            "Position-opening and position-closing option activity by origin type may add information beyond option volume, momentum and frozen LTM/F80; sign unspecified.",
            "NOM/industry volume share may determine whether venue-specific origin flow is stable or only reflects changing venue share.",
            "Professional, Customer and Firm origin categories may have different predictive content, but none identifies a named institution.",
            "NOP may serve as a related-source benchmark but is not independent confirmation of NOTO.",
        ],
        "required_next_gates": [
            "explicit authorization for sample, trial, purchase or terms acceptance",
            "resolve official ad-hoc historical pricing discrepancy",
            "raw EOD files across early, middle and recent history with actual first receipt and revision policy",
            "effective-dated option-series master including adjusted/non-standard contracts",
            "per-series NOM and total-industry coverage against frozen F80 universe",
            "origin/open-close field completeness and historical schema stability",
            "prospective capture of cumulative intraday snapshots if intraday is pursued",
            "fresh chronological OOS protocol with identical exposure/costs, bootstrap/LOO and multiplicity controls",
        ],
    }


def validate_result(result: dict[str, Any]) -> None:
    assert result["phase"] == 286
    c = result["controls"]
    for key in (
        "raw_data_downloaded", "api_key_used", "vendor_contacted", "trial_started",
        "license_or_terms_accepted", "pit_admission", "alpha_admission", "holdout_used",
        "production_changed", "universe_changed", "capital_changed", "parameters_changed",
    ):
        assert c[key] is False, key
    assert c["f80_frozen"] is True

    noto = result["noto"]
    assert noto["history_start"] == "2011-11"
    assert noto["eod"]["availability"].startswith("next business day")
    assert noto["eod"]["includes_total_industry_volume"] is True
    assert noto["intraday"]["frequency"] == "10-minute"
    assert noto["intraday"]["snapshots_are_cumulative"] is True
    assert noto["opening_closing_semantics"]["is_aggressor_side"] is False
    assert noto["professional_is_institutional_identity"] is False
    assert noto["named_beneficial_owner_available"] is False
    assert noto["fees_usd"]["ad_hoc_historical_price_conflict"]["resolved"] is False
    assert noto["pit_admitted"] is False and noto["alpha_admitted"] is False

    family = result["nasdaq_options_trade_outline_family"]
    assert len(family["advertised_venues"]) == 6
    assert family["all_venues_have_identical_schema_and_history"] is False
    assert family["combined_panel_admitted"] is False

    nop = result["nasdaq_options_pulse"]
    assert nop["history_start"] == "2019-01"
    assert nop["frequency"] == "10-minute"
    assert nop["independent_of_noto"] is False
    assert nop["pit_admitted"] is False and nop["alpha_admitted"] is False


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
