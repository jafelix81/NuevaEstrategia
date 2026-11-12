#!/usr/bin/env python3
"""Phase 310: strengthen raw SEC N-PORT sample retrieval with sign, series and PIT-bound checks.

Phase 193 performs the SEC retrieval and hashes the original bytes. This layer
reconciles its result against the purposive accession fixture, verifies that
expected CUSIPs occur on sign-concordant direct-short rows, and computes a
conservative next-full-XNYS-session candidate. It does not establish first
public receipt, broad universe coverage, or alpha.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import exchange_calendars as xc
import pandas as pd

DEFAULT_EVIDENCE = Path("research/phase193_nport_raw_filing_retrieval.json")
DEFAULT_INPUT = Path("phase193_output/phase193_nport_raw_filing_audit.json")
DEFAULT_OUTPUT = Path("phase310_output/phase310_nport_raw_vintage_validation.json")


def _valid_sha(value: Any) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", str(value or "").lower()))


def _next_full_xnys_session(acceptance_utc: str) -> str:
    accepted = pd.Timestamp(acceptance_utc)
    if accepted.tzinfo is None:
        raise ValueError("acceptance_timestamp_must_be_timezone_aware")
    start = accepted.tz_convert("America/New_York").date() + timedelta(days=1)
    end = start + timedelta(days=14)
    cal = xc.get_calendar("XNYS")
    sessions = cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    if len(sessions) == 0:
        raise ValueError("no_xnys_session_found_after_acceptance")
    return str(pd.Timestamp(sessions[0]).date())


def _accession_result_map(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = summary.get("accession_results", [])
    result = {}
    for row in rows:
        accession = str(row.get("accession", ""))
        if not accession or accession in result:
            raise ValueError("missing_or_duplicate_accession_result")
        result[accession] = row
    return result


def build_validation(summary: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    expected_items = evidence.get("accessions", [])
    actual = _accession_result_map(summary)
    expected_accessions = [str(x["accession"]) for x in expected_items]
    if len(set(expected_accessions)) != len(expected_accessions):
        raise ValueError("duplicate_accession_in_evidence_fixture")

    accession_audits = []
    all_raw = True
    all_headers = True
    all_series = True
    all_expected_sign = True
    sign_gate_known = True

    for item in expected_items:
        accession = str(item["accession"])
        row = actual.get(accession)
        if row is None or not row.get("raw_files_staged_for_artifact"):
            all_raw = False
            all_headers = False
            all_series = False
            all_expected_sign = False
            sign_gate_known = False
            accession_audits.append({
                "accession": accession,
                "status": "RAW_MISSING_OR_NOT_RETRIEVED",
                "expected_cusips": sorted(item.get("expected_cusips", [])),
                "expected_cusip_sign_gate": "UNKNOWN",
            })
            continue

        files = row.get("files", {})
        hashes = {
            "index": row.get("index_sha256"),
            "filing_index_html": row.get("filing_index_sha256"),
            "submission": row.get("submission_sha256"),
            "primary_xml": row.get("primary_xml_sha256"),
        }
        hash_ok = all(_valid_sha(v) for v in hashes.values())
        sizes_ok = all(int(row.get(k, 0) or 0) > 0 for k in (
            "index_bytes", "filing_index_bytes", "submission_bytes", "primary_xml_bytes"
        ))
        raw_ok = hash_ok and sizes_ok and bool(row.get("raw_files_staged_for_artifact"))
        all_raw = all_raw and raw_ok

        header = row.get("submission_header", {})
        header_ok = (
            header.get("header_accession_reconciled") == "true"
            and header.get("header_form_reconciled") == "true"
            and bool(header.get("acceptance_datetime_utc"))
            and header.get("acceptance_date_matches_filed_date") is True
        )
        all_headers = all_headers and header_ok

        xml = row.get("xml_audit", {})
        index_meta = row.get("filing_index_metadata", {})
        xml_series_ids = sorted(set(str(x) for x in xml.get("series_ids", []) if str(x)))
        index_series_ids = sorted(set(str(x) for x in index_meta.get("series_ids", []) if str(x)))
        series_ids = sorted(set(xml_series_ids) | set(index_series_ids))
        series_ok = len(series_ids) >= 1
        all_series = all_series and series_ok

        expected_cusips = sorted(set(str(x).strip().upper() for x in item.get("expected_cusips", []) if str(x).strip()))
        sample = xml.get("direct_short_rows_sample", [])
        truncated = bool(xml.get("direct_short_rows_sample_truncated"))
        sign_rows = [
            x for x in sample
            if x.get("sign_concordant") is True
            and str(x.get("units", "")).upper() == "NS"
            and x.get("cusip")
        ]
        sign_cusips = sorted(set(str(x["cusip"]).strip().upper() for x in sign_rows))
        if truncated:
            expected_sign_gate = "UNKNOWN_SAMPLE_TRUNCATED"
            sign_gate_known = False
            all_expected_sign = False
        else:
            missing = sorted(set(expected_cusips) - set(sign_cusips))
            expected_sign_gate = "PASS" if not missing else "FAIL"
            if missing:
                all_expected_sign = False
        missing_sign = sorted(set(expected_cusips) - set(sign_cusips))

        accepted = str(header.get("acceptance_datetime_utc", ""))
        next_session = _next_full_xnys_session(accepted) if accepted else None
        index_modified = str(row.get("index_listing", {}).get("primary_document_last_modified", ""))
        accepted_local = pd.Timestamp(accepted).tz_convert("America/New_York") if accepted else None
        index_clock_match = None
        if accepted_local is not None and index_modified:
            try:
                index_clock_match = pd.Timestamp(index_modified).to_pydatetime().replace(
                    tzinfo=accepted_local.tzinfo
                ) == accepted_local.to_pydatetime()
            except Exception:
                index_clock_match = None
        index_page_acceptance = index_meta.get("accepted_datetime_et")
        index_page_clock_match = None
        if accepted_local is not None and index_page_acceptance:
            index_page_clock_match = (
                accepted_local.strftime("%Y-%m-%dT%H:%M:%S") == str(index_page_acceptance)
            )

        accession_audits.append({
            "accession": accession,
            "cik": item.get("cik"),
            "filing_year": item.get("filing_year"),
            "raw_bytes_hash_and_artifact_gate": "PASS" if raw_ok else "FAIL",
            "sha256": hashes,
            "byte_sizes": {
                "index": row.get("index_bytes"),
                "filing_index_html": row.get("filing_index_bytes"),
                "submission": row.get("submission_bytes"),
                "primary_xml": row.get("primary_xml_bytes"),
            },
            "header_identity_and_acceptance_gate": "PASS" if header_ok else "FAIL",
            "submission_header_error": row.get("submission_header_error"),
            "submission_header_diagnostic": row.get("submission_header_diagnostic", {}),
            "acceptance_datetime_utc": accepted or None,
            "acceptance_date_matches_filed_date": header.get("acceptance_date_matches_filed_date"),
            "index_primary_last_modified": index_modified or None,
            "index_last_modified_matches_acceptance": index_clock_match,
            "index_page_accepted_datetime_et": index_page_acceptance,
            "index_page_acceptance_matches_header": index_page_clock_match,
            "submission_header_error": row.get("submission_header_error"),
            "submission_header_diagnostic": row.get("submission_header_diagnostic", {}),
            "conservative_next_full_xnys_session": next_session,
            "xml_series_ids": xml_series_ids,
            "index_series_ids": index_series_ids,
            "series_ids": series_ids,
            "series_gate": "PASS" if series_ok else "FAIL",
            "holding_nodes": xml.get("holding_nodes"),
            "direct_short_ec_corp_us_rows": xml.get("counts", {}).get("short_ec_corp_us_rows", 0),
            "sign_concordant_direct_short_rows_in_sample": len(sign_rows),
            "direct_short_sample_truncated": truncated,
            "expected_cusips": expected_cusips,
            "expected_cusips_found_sign_concordant": sorted(set(expected_cusips) & set(sign_cusips)),
            "expected_cusips_missing_sign_concordant": missing_sign,
            "expected_cusip_sign_gate": expected_sign_gate,
        })

    missing_results = sorted(set(expected_accessions) - set(actual))
    unexpected_results = sorted(set(actual) - set(expected_accessions))
    identity_set_ok = not missing_results and not unexpected_results
    raw_status = (
        "RAW_BYTES_HASHED_ACCEPTANCE_RECONCILED"
        if all_raw and all_headers and all_series and identity_set_ok
        else "PARTIAL_RAW_RETRIEVAL_OR_RECONCILIATION"
    )
    series_present_count = sum(1 for x in accession_audits if x.get("series_gate") == "PASS")
    series_missing_accessions = [
        str(x["accession"]) for x in accession_audits if x.get("series_gate") != "PASS"
    ]
    return {
        "phase": 310,
        "status": raw_status,
        "source_phase": 193,
        "source_sample_design": "purposive five-accession sample; not representative",
        "accessions_expected": len(expected_items),
        "accessions_reconciled": sum(1 for x in accession_audits if x.get("raw_bytes_hash_and_artifact_gate") == "PASS"),
        "accession_identity_set_gate": "PASS" if identity_set_ok else "FAIL",
        "missing_accession_results": missing_results,
        "unexpected_accession_results": unexpected_results,
        "raw_bytes_hash_and_artifact_gate": "PASS" if all_raw and identity_set_ok else "FAIL",
        "header_identity_acceptance_gate": "PASS" if all_headers and identity_set_ok else "FAIL",
        "series_identity_presence_gate": (
            "PASS" if all_series and identity_set_ok
            else "PARTIAL" if series_present_count > 0 and identity_set_ok
            else "FAIL"
        ),
        "series_identity_present_accessions": series_present_count,
        "series_identity_missing_accessions": series_missing_accessions,
        "expected_public_positive_control_sign_gate": (
            "PASS" if all_expected_sign and sign_gate_known and identity_set_ok
            else "FAIL" if sign_gate_known
            else "UNKNOWN"
        ),
        "accessions": accession_audits,
        "controls": {
            "first_public_receipt_verified": False,
            "strict_pit_admitted": False,
            "report_date_used_as_knowledge_date": False,
            "acceptance_is_first_public_time": False,
            "conservative_execution_boundary": "first full XNYS session strictly after SEC acceptance date; this is a conservative candidate, not proof of first public receipt",
            "amendment_lineage_complete": False,
            "effective_dated_security_master_complete": False,
            "broad_historical_universe_coverage": False,
            "representative_sample": False,
            "prevalence_estimated": False,
            "return_test_run": False,
            "alpha_test_authorized": False,
            "bootstrap_loo_run": False,
            "chronological_oos_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "email_sent": False,
            "raw_files_persisted_in_repository": False,
        },
        "decision": (
            "This phase validates only the five purposive NPORT-P filings. "
            "Raw bytes and hashes may pass while direct-short sign/CUSIP controls remain separate. "
            "Do not promote report-date positions to their report date. Preserve each accession as an "
            "as-filed vintage and use the conservative next-full-session candidate only after the "
            "filing-availability gate. No first-public receipt, amendment lineage, broad universe, "
            "strict PIT or alpha is admitted."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = json.loads(args.input.read_text(encoding="utf-8"))
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = build_validation(summary, evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
