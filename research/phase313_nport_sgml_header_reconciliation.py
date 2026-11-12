#!/usr/bin/env python3
"""Phase 313: correct SEC N-PORT SGML header identity parsing and re-audit Phase 312 offline.

The SEC submission header uses SGML-style tags such as <SERIES-ID>VALUE without
closing tags. Phase 312 searched for closing tags and therefore mislabeled
header/XML identity as XML_ONLY. This phase reuses immutable Phase 312 raw bytes,
verifies their recorded SHA-256 hashes, and corrects only the identity parsing.
No SEC requests or return tests are performed.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def unique_ordered(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _header_block(submission_text: str) -> str:
    return submission_text.split("<DOCUMENT>", 1)[0]


def _sgml_values(header_text: str, tag: str) -> list[str]:
    # SEC SGML headers commonly omit closing tags. Stop at whitespace or the
    # next '<' so both unclosed SGML and closed XML-like variants are safe.
    pattern = rf"<{re.escape(tag)}>\s*([^\s<]+)"
    return unique_ordered(re.findall(pattern, header_text, flags=re.IGNORECASE))


def parse_header_identity(submission_text: str) -> dict[str, list[str]]:
    header = _header_block(submission_text)
    names = unique_ordered(
        re.findall(r"<SERIES-NAME>\s*([^\r\n<]+)", header, flags=re.IGNORECASE)
    )
    return {
        "series_ids": _sgml_values(header, "SERIES-ID"),
        "class_ids": _sgml_values(header, "CLASS-CONTRACT-ID"),
        "series_names": names,
    }


def extract_primary_xml(submission_text: str, expected_form: str) -> str:
    blocks = re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", submission_text, flags=re.IGNORECASE | re.DOTALL)
    for block in blocks:
        type_match = re.search(r"<TYPE>\s*([^\r\n<]+)", block, flags=re.IGNORECASE)
        if not type_match or type_match.group(1).strip().upper() != expected_form.upper():
            continue
        xml_match = re.search(r"<XML>\s*(.*?)\s*</XML>", block, flags=re.IGNORECASE | re.DOTALL)
        if xml_match:
            return xml_match.group(1).strip()
        text_match = re.search(r"<TEXT>\s*(.*?)\s*</TEXT>", block, flags=re.IGNORECASE | re.DOTALL)
        if text_match:
            payload = text_match.group(1).strip()
            if payload.upper().startswith("<XML>"):
                payload = re.sub(r"^<XML>\s*|\s*</XML>$", "", payload, flags=re.IGNORECASE | re.DOTALL)
            if "<edgarSubmission" not in payload:
                raise ValueError("primary_nport_xml_root_missing")
            return payload
    raise ValueError("primary_nport_xml_document_not_found")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_values(root: ET.Element, name: str) -> list[str]:
    return unique_ordered([
        (element.text or "").strip()
        for element in root.iter()
        if local_name(element.tag) == name and (element.text or "").strip()
    ])


def identity_state(header_ids: list[str], xml_ids: list[str]) -> str:
    header_set, xml_set = set(header_ids), set(xml_ids)
    if not header_set and not xml_set:
        return "MISSING_BOTH"
    if header_set and not xml_set:
        return "HEADER_ONLY"
    if xml_set and not header_set:
        return "XML_ONLY"
    return "MATCH" if header_set == xml_set else "MISMATCH"


def ticker_overlap_state(ticker: str | None, frozen_tickers: set[str]) -> str:
    value = str(ticker or "").strip().upper()
    if not value or value in {"N/A", "NA", "NONE", "NULL"}:
        return "UNKNOWN_NOT_REPORTED"
    return "MATCH" if value in frozen_tickers else "NO_STRING_MATCH"


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_reconciliation(input_dir: Path, output_dir: Path, ticker_snapshot: Path) -> dict[str, Any]:
    filing_path = input_dir / "nport_sample_filing_reconciliation.csv"
    short_path = input_dir / "nport_short_candidate_rows.csv"
    result_path = input_dir / "phase312_nport_raw_sample_result.json"
    for required in (filing_path, short_path, result_path):
        if not required.is_file():
            raise FileNotFoundError(f"required_phase312_artifact_file_missing:{required.name}")

    previous_filings = _read_csv(filing_path)
    previous_short_rows = _read_csv(short_path)
    previous_result = json.loads(result_path.read_text(encoding="utf-8"))
    expected_short_rows = int(previous_result.get("holdings", {}).get("sign_concordant_short_rows", -1))
    if len(previous_short_rows) != expected_short_rows:
        raise ValueError(f"phase312_short_row_count_mismatch:{len(previous_short_rows)}:{expected_short_rows}")
    short_row_keys = {(row.get("accession"), row.get("row_number_within_short_candidates")) for row in previous_short_rows}
    if len(short_row_keys) != len(previous_short_rows):
        raise ValueError("phase312_short_row_keys_not_unique")
    if any(not _as_bool(row.get("sign_concordant")) for row in previous_short_rows):
        raise ValueError("phase312_short_csv_contains_nonconcordant_row")
    if len(previous_filings) != 56:
        raise ValueError(f"phase312_filing_rows_expected_56:{len(previous_filings)}")
    if len({row["accession"] for row in previous_filings}) != 56:
        raise ValueError("phase312_accessions_not_unique")
    if previous_result.get("phase") != 312 or previous_result.get("status") != "PASS_RAW_SAMPLE_CORE_RECONCILIATION":
        raise ValueError("phase312_source_result_not_expected_success")

    frozen_rows = _read_csv(ticker_snapshot)
    frozen_tickers = {row["ticker"].strip().upper() for row in frozen_rows if row.get("ticker")}
    if len(frozen_tickers) != 335:
        raise ValueError(f"frozen_legacy_ticker_count_expected_335:{len(frozen_tickers)}")
    ticker_sha256 = hashlib.sha256(ticker_snapshot.read_bytes()).hexdigest()

    corrected_filings: list[dict[str, Any]] = []
    identity_by_accession: dict[str, dict[str, Any]] = {}
    raw_hash_verified = 0

    for previous in previous_filings:
        accession = previous["accession"]
        raw_rel = previous.get("raw_file", "")
        if not raw_rel:
            raise ValueError(f"raw_file_path_missing:{accession}")
        raw_path = input_dir / raw_rel
        if not raw_path.is_file():
            raise FileNotFoundError(f"raw_submission_missing:{accession}")
        raw_bytes = raw_path.read_bytes()
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        if actual_sha != previous.get("raw_sha256"):
            raise ValueError(f"raw_sha256_mismatch:{accession}")
        raw_hash_verified += 1
        text = raw_bytes.decode("utf-8", errors="replace")

        header_ids = parse_header_identity(text)
        xml_text = extract_primary_xml(text, previous["form_type"])
        root = ET.fromstring(xml_text)
        xml_ids = {
            "series_ids": xml_values(root, "seriesId"),
            "class_ids": xml_values(root, "classId"),
            "series_names": xml_values(root, "seriesName"),
        }

        series_state = identity_state(header_ids["series_ids"], xml_ids["series_ids"])
        class_state = identity_state(header_ids["class_ids"], xml_ids["class_ids"])
        series_ids = unique_ordered(header_ids["series_ids"] + xml_ids["series_ids"])
        class_ids = unique_ordered(header_ids["class_ids"] + xml_ids["class_ids"])
        series_names = unique_ordered(header_ids["series_names"] + xml_ids["series_names"])

        row = dict(previous)
        row.update({
            "series_ids_header": json.dumps(header_ids["series_ids"]),
            "series_ids_xml": json.dumps(xml_ids["series_ids"]),
            "series_ids": json.dumps(series_ids),
            "series_identity_state": series_state,
            "class_ids_header": json.dumps(header_ids["class_ids"]),
            "class_ids_xml": json.dumps(xml_ids["class_ids"]),
            "class_ids": json.dumps(class_ids),
            "class_identity_state": class_state,
            "series_names_header": json.dumps(header_ids["series_names"]),
            "series_names_xml": json.dumps(xml_ids["series_names"]),
            "series_names": json.dumps(series_names),
            "series_header_xml_match": series_state == "MATCH" or series_state == "MISSING_BOTH",
            "class_header_xml_match": class_state == "MATCH" or class_state == "MISSING_BOTH",
            "raw_sha256_reverified": True,
        })
        corrected_filings.append(row)
        identity_by_accession[accession] = {
            "series_ids": series_ids,
            "class_ids": class_ids,
            "series_identity_state": series_state,
            "class_identity_state": class_state,
            "series_names": series_names,
        }

    corrected_short_rows: list[dict[str, Any]] = []
    ticker_overlap_counts = Counter()
    for previous in previous_short_rows:
        accession = previous["accession"]
        identity = identity_by_accession.get(accession)
        if identity is None:
            raise ValueError(f"short_row_accession_not_in_filing_panel:{accession}")
        row = dict(previous)
        row["series_ids"] = ";".join(identity["series_ids"])
        row["series_identity_state"] = identity["series_identity_state"]
        overlap_state = ticker_overlap_state(row.get("ticker"), frozen_tickers)
        row["legacy_ticker_string_overlap"] = overlap_state
        if _as_bool(row.get("sign_concordant")):
            ticker_overlap_counts[overlap_state] += 1
        corrected_short_rows.append(row)

    series_states = Counter(row["series_identity_state"] for row in corrected_filings)
    class_states = Counter(row["class_identity_state"] for row in corrected_filings)
    series_mismatches = [row["accession"] for row in corrected_filings if row["series_identity_state"] == "MISMATCH"]
    class_mismatches = [row["accession"] for row in corrected_filings if row["class_identity_state"] == "MISMATCH"]
    if series_mismatches or class_mismatches:
        raise ValueError("header_xml_identity_mismatch_fail_closed")

    short_rows = [row for row in corrected_short_rows if _as_bool(row.get("sign_concordant"))]
    positive_filings = []
    for row in corrected_filings:
        count = int(row.get("short_sign_concordant_rows") or 0)
        if count <= 0:
            continue
        report_date = row.get("xml_report_date") or ""
        filing_date = row.get("master_index_filing_date") or ""
        lag_days = None
        if report_date and filing_date:
            lag_days = (date.fromisoformat(filing_date) - date.fromisoformat(report_date)).days
        rows_for_accession = [x for x in short_rows if x["accession"] == row["accession"]]
        positive_filings.append({
            "accession": row["accession"],
            "form_type": row["form_type"],
            "registrant_cik": row["registrant_cik"],
            "company_name": row["company_name"],
            "report_date": report_date,
            "filing_date": filing_date,
            "report_to_filing_lag_calendar_days": lag_days,
            "series_ids": identity_by_accession[row["accession"]]["series_ids"],
            "series_identity_state": row["series_identity_state"],
            "short_rows": count,
            "ticker_reported_rows": sum(1 for x in rows_for_accession if x.get("ticker")),
            "cusip_check_digit_rows": sum(1 for x in rows_for_accession if _as_bool(x.get("cusip_check_digit_valid"))),
            "isin_check_digit_rows": sum(1 for x in rows_for_accession if _as_bool(x.get("isin_check_digit_valid"))),
        })

    unique_cusips = {row["cusip"] for row in short_rows if _as_bool(row.get("cusip_check_digit_valid")) and row.get("cusip")}
    unique_isins = {row["isin"] for row in short_rows if _as_bool(row.get("isin_check_digit_valid")) and row.get("isin")}
    unique_tickers = {row["ticker"].strip().upper() for row in short_rows if row.get("ticker")}
    ticker_reported = ticker_overlap_counts.get("MATCH", 0) + ticker_overlap_counts.get("NO_STRING_MATCH", 0)
    ticker_matches = ticker_overlap_counts.get("MATCH", 0)
    cusips_by_accession = {
        accession: {row["cusip"] for row in short_rows if row["accession"] == accession and row.get("cusip")}
        for accession in sorted({row["accession"] for row in short_rows})
    }
    accession_pairs = list(cusips_by_accession)
    cross_filing_cusip_overlap = sorted(
        cusips_by_accession[accession_pairs[0]] & cusips_by_accession[accession_pairs[1]]
    ) if len(accession_pairs) == 2 else []

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "nport_sample_filing_reconciliation_corrected.csv", corrected_filings, list(corrected_filings[0].keys()))
    _write_csv(output_dir / "nport_short_candidate_rows_corrected.csv", corrected_short_rows, list(corrected_short_rows[0].keys()))

    result = {
        "phase": 313,
        "status": "PASS_SGML_HEADER_XML_IDENTITY_RECONCILIATION",
        "source_phase": 312,
        "source_run_id": 43157888685,
        "source_artifact_id": 13915839847,
        "source_artifact_sha256": "78586bd1dbbbd12473ce6d0f75cdee360991541e99a9e2eb45641005f81a4287",
        "source_artifact_size_bytes": 12025039,
        "phase312_series_class_identity_labels_superseded": True,
        "expected_filings": 56,
        "parsed_filings": len(corrected_filings),
        "raw_sha256_verified": raw_hash_verified,
        "raw_bytes_modified": False,
        "series_identity_states": dict(series_states),
        "class_identity_states": dict(class_states),
        "series_header_xml_mismatches": len(series_mismatches),
        "class_header_xml_mismatches": len(class_mismatches),
        "series_ids_present": sum(1 for row in corrected_filings if json.loads(row["series_ids"])),
        "class_ids_present": sum(1 for row in corrected_filings if json.loads(row["class_ids"])),
        "series_names_present": sum(1 for row in corrected_filings if json.loads(row["series_names"])),
        "holdings": {
            "total_sign_concordant_short_rows": len(short_rows),
            "positive_filings": positive_filings,
            "positive_filing_count": len(positive_filings),
            "unique_cusips_check_digit_valid": len(unique_cusips),
            "unique_isins_check_digit_valid": len(unique_isins),
            "unique_tickers_reported": len(unique_tickers),
            "ticker_reported_rows": ticker_reported,
            "ticker_string_overlap_with_legacy_335": ticker_matches,
            "ticker_string_nonmatch_with_legacy_335": ticker_overlap_counts.get("NO_STRING_MATCH", 0),
            "ticker_unreported_rows": ticker_overlap_counts.get("UNKNOWN_NOT_REPORTED", 0),
            "cross_filing_cusip_overlap_count": len(cross_filing_cusip_overlap),
            "cross_filing_cusip_overlap": cross_filing_cusip_overlap,
            "legacy_ticker_snapshot_count": len(frozen_tickers),
            "legacy_ticker_snapshot_sha256": ticker_sha256,
            "ticker_string_overlap_is_not_pit_security_coverage": True,
            "cusip_only_rows_not_forced_to_ticker": True,
        },
        "sample_design": {
            "filings": 56,
            "selection": "one deterministic SHA-256 minimum per filing quarter and exact data-bearing form",
            "representative_prevalence_sample": False,
            "prevalence_estimate_authorized": False,
        },
        "controls": {
            "first_public_timestamp_admitted": False,
            "acceptance_treated_as_first_public_timestamp": False,
            "amendment_parent_linking_attempted": False,
            "fund_position_interpreted_as_trade": False,
            "effective_dated_security_master_complete": False,
            "f80_universe_coverage_measured": False,
            "return_test": False,
            "alpha_test": False,
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
        "interpretation": (
            "Phase 312's series/class identity state labels were wrong because the SEC SGML header "
            "uses unclosed tags. The immutable raw files show 53/56 header/XML MATCH and 3/56 "
            "MISSING_BOTH for both series and class identifiers. The three missing cases remain "
            "fund/CIK/name-level only; no series key is invented. The two sampled filings with "
            "short rows account for 176 rows, but the 56-filing sample is not representative and "
            "cannot estimate prevalence. The 335-ticker comparison is string overlap only; rows "
            "without reported ticker remain unknown. N-PORT positions are delayed fund snapshots, "
            "not trades or proof of informed behavior."
        ),
    }
    (output_dir / "phase313_nport_sgml_header_identity_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("phase312_input"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase313_output"))
    parser.add_argument(
        "--ticker-snapshot",
        type=Path,
        default=Path("research/phase313_f80_legacy_ticker_snapshot_2026-10-20.csv"),
    )
    args = parser.parse_args()
    try:
        result = run_reconciliation(args.input_dir, args.output_dir, args.ticker_snapshot)
    except Exception as exc:
        print(f"PHASE313_FAIL={type(exc).__name__}:{exc}", file=sys.stderr, flush=True)
        raise
    print(json.dumps({
        "phase": 313,
        "status": result["status"],
        "parsed_filings": result["parsed_filings"],
        "raw_sha256_verified": result["raw_sha256_verified"],
        "series_identity_states": result["series_identity_states"],
        "class_identity_states": result["class_identity_states"],
        "short_rows": result["holdings"]["total_sign_concordant_short_rows"],
        "positive_filings": result["holdings"]["positive_filing_count"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
