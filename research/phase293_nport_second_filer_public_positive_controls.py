#!/usr/bin/env python3
"""Phase 293: replay a second SEC N-PORT filer through the hardened row classifier."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.phase221_nport_absence_semantics_audit import classify_direct_short_state
from research.phase292_nport_short_classification_hardening import build_audit as build_phase292_audit

FIXTURE = Path(__file__).with_name("phase217_nport_full_submission_text_short_row_pilot.json")


def build_audit() -> dict:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    filing = fixture["filing"]
    rows = fixture["selected_rows"]
    if filing["accession"] != "0001145549-25-033457":
        raise ValueError("unexpected_second_filer_accession")
    if filing["registrant_cik"] != "0001467631":
        raise ValueError("unexpected_second_filer_cik")
    if filing["period_of_report"] != "2025-03-31":
        raise ValueError("unexpected_second_filer_report_date")
    if len(rows) != 23:
        raise ValueError("second_filer_selected_row_count_changed")
    cusips = [str(row["cusip"]).strip().upper() for row in rows]
    if len(set(cusips)) != len(cusips):
        raise ValueError("duplicate_cusip_in_selected_second_filer_rows")

    for row in rows:
        if not (
            row["payoff_profile"] == "Short"
            and row["units"] == "NS"
            and row["asset_category"] == "EC"
            and row["issuer_category"] == "CORP"
            and row["investment_country"] == "US"
            and row["balance"] < 0
            and row["val_usd"] < 0
            and row["pct_nav"] < 0
            and len(str(row["cusip"])) == 9
            and row["source_line_start"] <= row["source_line_end"]
        ):
            raise ValueError("second_filer_fixture_invariant_failed:" + row["name"])

        classifier_row = {
            "payoff_profile": row["payoff_profile"],
            "unit": row["units"],
            "asset_cat": row["asset_category"],
            "issuer_cat": row["issuer_category"],
            "investment_country": row["investment_country"],
            "cusip": row["cusip"],
            "isin": None,
            "balance": row["balance"],
            "currency_value": row["val_usd"],
            "percentage": row["pct_nav"],
        }
        result = classify_direct_short_state(
            prior_public_part_c=False,
            current_period_public=True,
            current_filing_complete=True,
            same_series=True,
            same_security=True,
            corporate_action_clear=True,
            current_vintage_as_of_signal=True,
            part_d_ineligible_due_prior_public=False,
            current_part_c_rows=[classifier_row],
            expected_cusip=row["cusip"],
            expected_isin=None,
        )
        if result["status"] != "OBSERVED_SHORT_POSITION":
            raise ValueError("second_filer_positive_control_failed:" + row["name"])

    phase292 = build_phase292_audit()
    phase291_fixture = json.loads(
        (Path(__file__).with_name("phase291_nport_public_short_positive_control.json")).read_text(encoding="utf-8")
    )
    first_cik = phase291_fixture["filing"]["cik"]
    second_cik = filing["registrant_cik"]
    if first_cik == second_cik:
        raise ValueError("positive_controls_not_independent_registrants")

    return {
        "phase": 293,
        "status": "NPORT_HARDENED_CLASSIFIER_TWO_PUBLIC_FILERS_26_SELECTED_ROWS_PASS_NO_RAW_BYTES_NO_ALPHA",
        "public_filings": [
            {
                "accession": phase291_fixture["filing"]["accession"],
                "cik": first_cik,
                "fund": phase291_fixture["filing"]["fund_name"],
                "report_date": phase291_fixture["filing"]["report_date"],
                "selected_positive_rows": len(phase291_fixture["positions"]),
                "series_id": phase291_fixture["filing"]["series_id"],
                "evidence_mode": "MANUAL_TRANSCRIPTION_OF_SEC_RENDERED_PRIMARY_XML",
            },
            {
                "accession": filing["accession"],
                "cik": second_cik,
                "fund": filing["fund_name"],
                "report_date": filing["period_of_report"],
                "selected_positive_rows": len(rows),
                "series_id_present": False,
                "evidence_mode": "MANUAL_LINE_REFERENCED_COMPLETE_SUBMISSION_TEXT_FIXTURE_AND_RENDERED_XML_SPOT_CHECK",
            },
        ],
        "distinct_registrants": 2,
        "public_positive_controls_passed": len(phase291_fixture["positions"]) + len(rows),
        "phase293_second_filer_positive_controls_passed": len(rows),
        "phase292_negative_controls_passed": phase292["negative_controls_passed"],
        "second_filer_selected_rows_exhaustive": False,
        "prevalence_estimated": False,
        "raw_xml_bytes_downloaded": False,
        "raw_xml_sha256_verified": False,
        "complete_submission_raw_sha256_verified": False,
        "first_public_receipt_verified": False,
        "series_longitudinal_identity_established": False,
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
        "decision": "ROW_CLASSIFIER_GENERALIZES_TO_SECOND_PUBLIC_FILER_FIXTURE_ONLY; KEEP_NPORT_UNADMITTED_PENDING_RAW_BYTES_PIT_LINEAGE_AND_BROAD_COVERAGE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase293_output/summary.json"))
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
