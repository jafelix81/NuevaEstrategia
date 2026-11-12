#!/usr/bin/env python3
"""Phase 315: reconcile N-PORT identifier value attributes against Phase 312 parser.

Uses the immutable Phase 314 artifact only. No new SEC requests are made.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from research.phase312_nport_raw_sample_audit import (
    cusip_check_digit_valid,
    isin_check_digit_valid,
    parse_holding_rows,
)
from research.phase314_nport_amendment_parent_audit import (
    compare_positions,
    extract_primary_xml,
    parse_submission,
)

PHASE314_RUN_ID = 43160951691
PHASE314_ARTIFACT_ID = 13917229995
PHASE314_ARTIFACT_SHA256 = "ec1a61d1172350778b9da1d4ef0e49f25a6279c1b3b328747992fdccc92ebe2b"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_hash(raw: bytes, expected: str, label: str) -> str:
    actual = sha256_bytes(raw)
    if actual != expected:
        raise ValueError(f"sha256_mismatch:{label}:{actual}:{expected}")
    return actual


def phase314_signature(row: dict[str, str]) -> tuple[str, ...]:
    return (
        row.get("cusip", ""),
        row.get("isin", ""),
        row.get("ticker", ""),
        row.get("balance", ""),
        row.get("value_usd", ""),
        row.get("percentage_nav", ""),
    )


def phase312_signature(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        row.get("cusip", ""),
        row.get("isin", ""),
        row.get("ticker", ""),
        row.get("balance", ""),
        row.get("currency_value_usd", ""),
        row.get("percentage_nav", ""),
    )


def parse_and_crosscheck(raw: bytes, expected_form: str, label: str) -> tuple[dict[str, Any], int]:
    parsed = parse_submission(raw, expected_form)
    xml_text = extract_primary_xml(raw.decode("utf-8", errors="replace"), expected_form)
    root = ET.fromstring(xml_text)
    reference_rows, holding_nodes = parse_holding_rows(root)
    reference_short = [row for row in reference_rows if row.get("sign_concordant")]
    phase_rows = parsed["short_positions"]
    if sorted(phase314_signature(row) for row in phase_rows) != sorted(
        phase312_signature(row) for row in reference_short
    ):
        raise ValueError(f"phase312_phase314_position_mismatch:{label}")
    return parsed, holding_nodes


def identifier_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "cusip_present": sum(bool(row.get("cusip")) for row in rows),
        "isin_present": sum(bool(row.get("isin")) for row in rows),
        "ticker_present": sum(bool(row.get("ticker")) for row in rows),
        "cusip_check_digit_valid": sum(cusip_check_digit_valid(row.get("cusip", "")) for row in rows),
        "isin_check_digit_valid": sum(isin_check_digit_valid(row.get("isin", "")) for row in rows),
    }


def exposure_metrics(rows: list[dict[str, str]]) -> dict[str, str]:
    abs_value = sum((abs(Decimal(row["value_usd"])) for row in rows), Decimal("0"))
    abs_pct = sum((abs(Decimal(row["percentage_nav"])) for row in rows), Decimal("0"))
    return {
        "absolute_reported_short_value_usd": str(abs_value),
        "absolute_reported_short_pct_nav_points": str(abs_pct),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_audit(input_dir: Path, output_dir: Path) -> dict[str, Any]:
    source_result_path = input_dir / "phase314_otter_creek_parent_audit_result.json"
    source_result = json.loads(source_result_path.read_text(encoding="utf-8"))
    if source_result.get("phase") != 314 or source_result.get("status") != "PASS_OTTER_CREEK_PARENT_CANDIDATE_AUDIT":
        raise ValueError("phase314_source_result_invalid")

    candidate_csv = input_dir / "candidate_originals_reconciliation.csv"
    with candidate_csv.open("r", newline="", encoding="utf-8") as handle:
        candidate_rows = list(csv.DictReader(handle))
    if len(candidate_rows) != source_result["candidate_count"]:
        raise ValueError("candidate_count_mismatch")

    candidate_summary: list[dict[str, Any]] = []
    all_candidate_short: list[dict[str, str]] = []
    parsed_by_accession: dict[str, dict[str, Any]] = {}
    crosschecked_documents = 0

    for row in candidate_rows:
        raw_path = input_dir / row["raw_file"]
        raw = raw_path.read_bytes()
        verify_hash(raw, row["raw_sha256"], row["accession"])
        parsed, holding_nodes = parse_and_crosscheck(raw, row["form_type"], row["accession"])
        crosschecked_documents += 1
        if parsed["accession"] != row["accession"]:
            raise ValueError(f"candidate_accession_mismatch:{row['accession']}")
        if parsed["registrant_cik"] != row["registrant_cik"].zfill(10):
            raise ValueError(f"candidate_cik_mismatch:{row['accession']}")
        if parsed["filed_as_of_date"] != row["filed_as_of_date"]:
            raise ValueError(f"candidate_filed_date_mismatch:{row['accession']}")
        if parsed["report_date"] != row["report_date"]:
            raise ValueError(f"candidate_report_date_mismatch:{row['accession']}")
        if parsed["series_identity_state"] != "MATCH" or parsed["class_identity_state"] != "MATCH":
            raise ValueError(f"candidate_identity_not_matched:{row['accession']}")
        positions = parsed["short_positions"]
        if len(positions) != int(row["short_rows"]):
            raise ValueError(f"candidate_short_row_count_mismatch:{row['accession']}")
        parsed_by_accession[row["accession"]] = parsed
        all_candidate_short.extend(positions)
        metrics = identifier_metrics(positions)
        candidate_summary.append({
            "accession": row["accession"],
            "filing_date": row["filing_date"],
            "report_date": row["report_date"],
            "series_ids": ";".join(parsed["series_ids"]),
            "series_identity_state": parsed["series_identity_state"],
            "class_identity_state": parsed["class_identity_state"],
            "holding_nodes": holding_nodes,
            "short_rows": len(positions),
            "cusip_present": metrics["cusip_present"],
            "isin_present": metrics["isin_present"],
            "ticker_present": metrics["ticker_present"],
            "cusip_check_digit_valid": metrics["cusip_check_digit_valid"],
            "isin_check_digit_valid": metrics["isin_check_digit_valid"],
            "raw_sha256": row["raw_sha256"],
        })

    parent_meta = source_result["parent_linkage"]["matches"][0]
    parent_accession = parent_meta["accession"]
    parent = parsed_by_accession[parent_accession]
    parent_raw = (input_dir / "unique_parent_candidate_raw.txt").read_bytes()
    verify_hash(parent_raw, parent_meta["raw_sha256"], "unique_parent_candidate_raw")
    if sha256_bytes(parent_raw) != sha256_bytes((input_dir / parent_meta["raw_file"]).read_bytes()):
        raise ValueError("parent_duplicate_raw_bytes_differ")

    amendment_meta = source_result["target_amendment"]
    amendment_raw = (input_dir / "target_amendment_raw.txt").read_bytes()
    verify_hash(amendment_raw, amendment_meta["sha256"], "target_amendment_raw")
    amendment, amendment_holding_nodes = parse_and_crosscheck(amendment_raw, "NPORT-P/A", "target_amendment")

    control_meta = source_result["2023_same_series_control"]
    control_raw = (input_dir / "same_series_2023_raw.txt").read_bytes()
    verify_hash(control_raw, control_meta["sha256"], "same_series_2023_raw")
    control, control_holding_nodes = parse_and_crosscheck(control_raw, "NPORT-P", "same_series_2023_control")

    if amendment["series_ids"] != parent["series_ids"] or control["series_ids"] != parent["series_ids"]:
        raise ValueError("same_series_identity_mismatch")
    if amendment["report_date"] != parent["report_date"]:
        raise ValueError("amendment_report_date_mismatch")

    original_vs_amendment = compare_positions(parent["short_positions"], amendment["short_positions"])
    amendment_vs_2023 = compare_positions(amendment["short_positions"], control["short_positions"])
    expected_original = {"left_rows": 20, "right_rows": 20, "unchanged_rows": 20, "modified_rows": 0, "added_rows": 0, "removed_rows": 0}
    expected_cross = {"left_rows": 20, "right_rows": 27, "unchanged_rows": 0, "modified_rows": 4, "added_rows": 23, "removed_rows": 16}
    for key, value in expected_original.items():
        if original_vs_amendment.get(key) != value:
            raise ValueError(f"original_amendment_comparison_changed:{key}")
    for key, value in expected_cross.items():
        if amendment_vs_2023.get(key) != value:
            raise ValueError(f"cross_period_comparison_changed:{key}")

    position_rows: list[dict[str, Any]] = []
    for role, parsed in [
        ("2022_ORIGINAL", parent),
        ("2022_AMENDMENT", amendment),
        ("2023_SAME_SERIES_CONTROL", control),
    ]:
        for row in parsed["short_positions"]:
            position_rows.append({
                "filing_role": role,
                "accession": parsed["accession"],
                "filing_date": parsed["filed_as_of_date"],
                "report_date": parsed["report_date"],
                "series_id": ";".join(parsed["series_ids"]),
                **row,
            })

    parent_metrics = identifier_metrics(parent["short_positions"])
    amendment_metrics = identifier_metrics(amendment["short_positions"])
    control_metrics = identifier_metrics(control["short_positions"])
    positive_candidate_docs = sum(1 for row in candidate_summary if row["short_rows"] > 0)
    if positive_candidate_docs != 1 or len(all_candidate_short) != 20:
        raise ValueError("registrant_quarter_short_position_census_unexpected")
    for label, metrics in [
        ("parent", parent_metrics),
        ("amendment", amendment_metrics),
        ("2023_control", control_metrics),
    ]:
        if metrics["cusip_present"] != metrics["rows"] or metrics["isin_present"] != metrics["rows"] or metrics["ticker_present"] != metrics["rows"]:
            raise ValueError(f"identifier_completeness_failed:{label}")
        if metrics["cusip_check_digit_valid"] != metrics["rows"] or metrics["isin_check_digit_valid"] != metrics["rows"]:
            raise ValueError(f"identifier_check_digit_failed:{label}")

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        output_dir / "candidate_cohort_identifier_audit.csv",
        candidate_summary,
        ["accession","filing_date","report_date","series_ids","series_identity_state","class_identity_state","holding_nodes","short_rows","cusip_present","isin_present","ticker_present","cusip_check_digit_valid","isin_check_digit_valid","raw_sha256"],
    )
    write_csv(
        output_dir / "short_positions_reconciled.csv",
        position_rows,
        ["filing_role","accession","filing_date","report_date","series_id","issuer_name","issue_title","cusip","isin","ticker","balance","value_usd","percentage_nav","payoff_profile","asset_category","issuer_type","investment_country","units"],
    )

    result = {
        "phase": 315,
        "status": "PASS_ATTRIBUTE_IDENTIFIER_RECONCILIATION",
        "source": {
            "phase314_run_id": PHASE314_RUN_ID,
            "phase314_artifact_id": PHASE314_ARTIFACT_ID,
            "phase314_artifact_sha256": PHASE314_ARTIFACT_SHA256,
            "candidate_raw_files_hash_verified": len(candidate_rows),
            "crosschecked_documents_against_phase312_parser": crosschecked_documents + 2,
        },
        "candidate_cohort": {
            "registrant_cik": "0000811030",
            "quarter": "2022Q3",
            "form": "NPORT-P",
            "filings": len(candidate_rows),
            "filings_with_sign_concordant_short_rows": positive_candidate_docs,
            "sign_concordant_short_rows": len(all_candidate_short),
            "interpretation": "complete NPORT-P filing cohort for one registrant in one quarter; not a representative fund or market prevalence sample",
        },
        "identifier_metrics": {
            "2022_original": parent_metrics,
            "2022_amendment": amendment_metrics,
            "2023_same_series_control": control_metrics,
        },
        "exposure_metrics": {
            "2022_original": exposure_metrics(parent["short_positions"]),
            "2022_amendment": exposure_metrics(amendment["short_positions"]),
            "2023_same_series_control": exposure_metrics(control["short_positions"]),
        },
        "vintage_comparison": {
            "original_vs_amendment": original_vs_amendment,
            "amendment_vs_2023_same_series": amendment_vs_2023,
            "interpretation": "same-report amendment comparison is a correction-vintage check; 2022-to-2023 differences are between delayed portfolio snapshots and are not trades or trade dates",
        },
        "controls": {
            "phase312_reference_parser_reconciled": True,
            "raw_hashes_verified": True,
            "identifier_value_attributes_supported": True,
            "position_rows_are_trades": False,
            "cross_period_position_changes_are_trades": False,
            "report_date_is_knowledge_date": False,
            "acceptance_is_first_public_timestamp": False,
            "effective_dated_security_master_complete": False,
            "f80_universe_coverage_measured": False,
            "alpha_test": False,
            "return_test": False,
            "bootstrap": False,
            "loo": False,
            "chronological_oos": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "email_sent": False,
        },
    }
    (output_dir / "phase315_nport_position_identifier_attribute_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = run_audit(args.input_dir, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
