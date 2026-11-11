#!/usr/bin/env python3
"""Phase 292: harden N-PORT direct-short classification against false positives."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.phase221_nport_absence_semantics_audit import classify_direct_short_state

FIXTURE = Path(__file__).with_name("phase291_nport_public_short_positive_control.json")


def _base_inputs(row, position):
    return {
        "prior_public_part_c": False,
        "current_period_public": True,
        "current_filing_complete": True,
        "same_series": True,
        "same_security": True,
        "corporate_action_clear": True,
        "current_vintage_as_of_signal": True,
        "part_d_ineligible_due_prior_public": False,
        "current_part_c_rows": [row],
        "expected_cusip": position["cusip"],
        "expected_isin": position["isin"],
    }


def build_audit() -> dict:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    positions = fixture["positions"]
    if len(positions) != 3:
        raise ValueError("phase291_public_positive_control_count_changed")

    for position in positions:
        row = {
            "payoff_profile": position["payoff_profile"],
            "unit": position["unit_code"],
            "asset_cat": position["asset_cat_code"],
            "issuer_cat": position["issuer_cat_code"],
            "investment_country": position["investment_country"],
            "cusip": position["cusip"],
            "isin": position["isin"],
            "balance": position["balance_shares"],
            "currency_value": position["currency_value_usd"],
            "percentage": position["percentage_nav"],
        }
        result = classify_direct_short_state(**_base_inputs(row, position))
        if result["status"] != "OBSERVED_SHORT_POSITION":
            raise ValueError("public_positive_control_failed:" + position["ticker"])

    first = positions[0]
    base_row = {
        "payoff_profile": first["payoff_profile"],
        "unit": first["unit_code"],
        "asset_cat": first["asset_cat_code"],
        "issuer_cat": first["issuer_cat_code"],
        "investment_country": first["investment_country"],
        "cusip": first["cusip"],
        "isin": first["isin"],
        "balance": first["balance_shares"],
        "currency_value": first["currency_value_usd"],
        "percentage": first["percentage_nav"],
    }
    negatives = {
        "non_us_country": {**base_row, "investment_country": "CA"},
        "currency_value_sign_conflict": {**base_row, "currency_value": abs(base_row["currency_value"])},
        "percentage_sign_conflict": {**base_row, "percentage": abs(base_row["percentage"])},
        "wrong_cusip": {**base_row, "cusip": positions[1]["cusip"]},
        "missing_identifiers": {**base_row, "cusip": None, "isin": None},
    }
    for name, row in negatives.items():
        result = classify_direct_short_state(**_base_inputs(row, first))
        if result["status"] != "UNKNOWN":
            raise ValueError("negative_control_admitted:" + name)

    return {
        "phase": 292,
        "status": "NPORT_SHORT_CLASSIFIER_HARDENED_PUBLIC_RENDERED_XML_FIXTURE_PASS_NO_RAW_BYTES_NO_ALPHA",
        "source_filing_accession": fixture["filing"]["accession"],
        "source_evidence_mode": fixture.get("source_evidence_mode", "UNSPECIFIED"),
        "public_positive_controls_passed": len(positions),
        "negative_controls_passed": len(negatives),
        "required_row_fields": [
            "CUSIP_or_ISIN_exact_match",
            "UNIT_NS",
            "ASSET_CAT_EC",
            "ISSUER_TYPE_CORP",
            "INVESTMENT_COUNTRY_US",
            "PAYOFF_PROFILE",
            "BALANCE",
            "CURRENCY_VALUE",
            "PERCENTAGE",
        ],
        "raw_xml_bytes_downloaded": False,
        "raw_xml_sha256_verified": False,
        "sec_automated_requests_sent": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "return_test_run": False,
        "bootstrap_loo_run": False,
        "holdout_used": False,
        "f80_frozen": True,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "decision": "KEEP_NPORT_DIRECT_SHORT_UNADMITTED_PENDING_RAW_BYTES_AS_FILED_VINTAGE_SERIES_AND_EFFECTIVE_DATED_SECURITY_PANEL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase292_output/summary.json"))
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
