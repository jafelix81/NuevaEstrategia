#!/usr/bin/env python3
"""Phase 164: one effective-dated CUSIP transition control from Phase 149."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

CASE = {
    "issuer_cik": "0001341335",
    "old_issuer_name": "Fortuna Silver Mines Inc.",
    "new_issuer_name": "Fortuna Mining Corp.",
    "old_cusip": "349915108",
    "new_cusip": "349942102",
    "share_class_figi": "BBG001S982M0",
    "legal_name_effective_date": "2024-06-20",
    "legal_name_change_time_local": "11:46 Pacific",
    "tsx_identifier_effective_date": "2024-06-27",
    "old_cusip_last_valid_date_tsx": "2024-06-26",
    "new_cusip_first_valid_date_tsx": "2024-06-27",
    "tsx_ticker": "FVI",
    "nyse_ticker": "FSM",
    "nyse_identifier_effective_date": None,
    "tsx_date_verified": True,
    "nyse_date_verified": False,
    "openfigi_old_name": "FORTUNA SILVER MINES INC",
    "openfigi_old_tickers": ["FVI", "FVIG"],
    "openfigi_new_name": "FORTUNA MINING CORP",
    "openfigi_new_tickers": ["0QYM", "F4S0", "F4S0D", "FSM", "FVI", "FVI1EUR", "FVI1USD", "FVI2", "FVICAD", "FVICHF", "FVIEUR", "FVIGBP", "FVIN", "FVIPLN", "FVIUSD"],
    "openfigi_current_share_class_figi_equal": True,
    "phase149_input_cusips": 553,
    "phase149_primary_mapped": 438,
    "phase149_primary_no_match": 115,
    "phase149_fallback_attempted": 115,
    "phase149_fallback_unique_recovered": 6,
    "phase149_fallback_no_match": 109,
    "phase149_cross_cusip_shareclass_pairs": 1,
    "phase149_cross_cusip_pair_count": 2,
    "phase149_run_id": 42274313824,
    "phase149_artifact_id": 13531523894,
    "source_urls": [
        "https://www.sec.gov/Archives/edgar/data/1341335/000110465924073576/tm2417718d1_ex99-3.htm",
        "https://fortunamining.com/news/fortuna-reports-results-of-annual-and-special-meeting/",
        "https://www.stockwatch.com/News/Item/Z-C!FVI-3570525/C/FVI",
        "https://www.bmv.com.mx/es/emisoras/perfil/FVI-7476",
    ],
}


def legal_name_on_date(date: str) -> str:
    return CASE["old_issuer_name"] if date < CASE["legal_name_effective_date"] else CASE["new_issuer_name"]


def cusip_on_date(date: str, venue: str = "TSX") -> str | None:
    if venue.upper() != "TSX":
        return None
    return CASE["old_cusip"] if date < CASE["tsx_identifier_effective_date"] else CASE["new_cusip"]


def ticker_on_date(venue: str) -> str | None:
    venue = venue.upper()
    if venue == "TSX":
        return CASE["tsx_ticker"]
    if venue == "NYSE":
        return CASE["nyse_ticker"]
    return None


def audit() -> dict:
    valid = (
        CASE["old_cusip"] != CASE["new_cusip"]
        and CASE["openfigi_current_share_class_figi_equal"]
        and CASE["legal_name_effective_date"] < CASE["tsx_identifier_effective_date"]
        and CASE["old_cusip_last_valid_date_tsx"] < CASE["new_cusip_first_valid_date_tsx"]
        and CASE["tsx_identifier_effective_date"] == CASE["new_cusip_first_valid_date_tsx"]
        and CASE["tsx_date_verified"]
        and not CASE["nyse_date_verified"]
    )
    return {
        "phase": 164,
        "status": "MANUAL_CORPORATE_ACTION_BRIDGE_VERIFIED_TSX_ONLY" if valid else "INVALID_TRANSITION_FIXTURE",
        "sample_design": "SINGLE_TARGETED_CROSS_CUSIP_POSITIVE_CONTROL",
        "case": CASE,
        "old_cusip_last_valid_date_tsx": CASE["old_cusip_last_valid_date_tsx"],
        "new_cusip_first_valid_date_tsx": CASE["new_cusip_first_valid_date_tsx"],
        "legal_name_effective_date": CASE["legal_name_effective_date"],
        "legal_name_on_2024_06_19": legal_name_on_date("2024-06-19"),
        "legal_name_on_2024_06_20": legal_name_on_date("2024-06-20"),
        "tsx_cusip_on_2024_06_26": cusip_on_date("2024-06-26", "TSX"),
        "tsx_cusip_on_2024_06_27": cusip_on_date("2024-06-27", "TSX"),
        "nyse_cusip_on_2024_06_27": cusip_on_date("2024-06-27", "NYSE"),
        "tsx_ticker": ticker_on_date("TSX"),
        "nyse_ticker": ticker_on_date("NYSE"),
        "share_class_figi": CASE["share_class_figi"],
        "phase149_primary_mapping_rate": CASE["phase149_primary_mapped"] / CASE["phase149_input_cusips"],
        "phase149_primary_no_match_rate": CASE["phase149_primary_no_match"] / CASE["phase149_input_cusips"],
        "phase149_fallback_unique_recovery_rate_of_no_matches": CASE["phase149_fallback_unique_recovered"] / CASE["phase149_fallback_attempted"],
        "historical_ticker_backdating_allowed": False,
        "nyse_cusip_date_inferred": False,
        "forward_returns_used": False,
        "final_holdout_used": False,
        "production_changed": False,
        "f80_changed": False,
        "decision": "Add only this source-dated TSX transition as a manual security-master bridge. Keep legal name date separate from exchange identifier date. Do not infer an NYSE CUSIP date or backdate OpenFIGI current tickers.",
    }


def write_outputs(summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase164_cusip_transition_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    row = {
        "issuer_cik": CASE["issuer_cik"],
        "old_cusip": CASE["old_cusip"],
        "new_cusip": CASE["new_cusip"],
        "share_class_figi": CASE["share_class_figi"],
        "legal_name_effective_date": CASE["legal_name_effective_date"],
        "tsx_old_cusip_last_valid_date": CASE["old_cusip_last_valid_date_tsx"],
        "tsx_new_cusip_first_valid_date": CASE["new_cusip_first_valid_date_tsx"],
        "tsx_ticker": CASE["tsx_ticker"],
        "nyse_ticker": CASE["nyse_ticker"],
        "nyse_identifier_effective_date": "",
        "status": summary["status"],
    }
    with (output_dir / "phase164_cusip_transition_bridge.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    summary = audit()
    write_outputs(summary, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "MANUAL_CORPORATE_ACTION_BRIDGE_VERIFIED_TSX_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
