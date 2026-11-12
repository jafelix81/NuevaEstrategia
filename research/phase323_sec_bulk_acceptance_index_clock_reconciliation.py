#!/usr/bin/env python3
"""Phase 323: reconcile SEC legal filed-date, acceptance and daily-index clocks.

Consumes immutable Phase 322 parsed adjudication metadata. It corrects the
semantic comparison between SEC-HEADER FILED AS OF DATE and the daily-index
file/row date, and prospectively searches acceptance-date windows for the
three accessions still lacking a parsed daily-index hit. Raw SEC bytes are
hashed/parsed in memory only and are never uploaded.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.phase283_sec_daily_index_parser import parse_daily_form_index
from research.phase318_nport_next_business_day_clock import (
    is_edgar_business_day, next_edgar_business_day,
)
from research.phase320_sec_bulk_daily_index_join import (
    RetrievalError, _fetch_bytes, _index_path, index_url, normalize_accession,
    normalize_cik, sha256_bytes,
)

PHASE = 323
SOURCE_RUN_ID = 43187165781
SOURCE_ARTIFACT_ID = 13928752264
SOURCE_ARTIFACT_NAME = "phase322-sec-bulk-index-exception-adjudication"
SOURCE_ARTIFACT_SHA256 = "c7eaf3cfc751e401d543bceeec20c3fe6643b09dfb8d2b0ff97df86070dca50d"
EXPECTED_EXCEPTIONS = 24
MAX_ROUTINE_ACCEPTANCE_LAG_BUSINESS_DAYS = 5
ACCEPTANCE_SEARCH_BUSINESS_DAYS = 6
FORM_TYPES = {"4", "4/A"}


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fields:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            })


def read_source(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("phase") != 322 or result.get("exception_summary", {}).get("total") != EXPECTED_EXCEPTIONS:
        raise ValueError("phase322_source_artifact_identity_mismatch")
    if result.get("exception_summary", {}).get("all_cases_have_original_header") is not True:
        raise ValueError("phase322_original_header_gate_not_pass")
    if result.get("exception_summary", {}).get("all_cases_have_master_index_hit") is not True:
        raise ValueError("phase322_master_index_gate_not_pass")
    if len(result.get("cases", [])) != EXPECTED_EXCEPTIONS:
        raise ValueError("phase322_case_denominator_mismatch")
    return result


def acceptance_date_from_header(acceptance: str) -> str:
    if not re.fullmatch(r"\d{14}", acceptance or ""):
        return ""
    return datetime.strptime(acceptance, "%Y%m%d%H%M%S").date().isoformat()


def business_day_lag(start_text: str, end_text: str) -> int | None:
    if not start_text or not end_text:
        return None
    start = date.fromisoformat(start_text)
    end = date.fromisoformat(end_text)
    if end < start:
        return None
    count = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if is_edgar_business_day(current):
            count += 1
    return count


def candidate_dates_from_acceptance(acceptance_date: str, count: int = ACCEPTANCE_SEARCH_BUSINESS_DAYS) -> list[str]:
    if not acceptance_date:
        return []
    current = date.fromisoformat(acceptance_date)
    values = [current.isoformat()]
    for _ in range(count - 1):
        current = next_edgar_business_day(current)
        values.append(current.isoformat())
    return values


def raw_line_matches(raw: bytes, accession: str) -> list[dict]:
    """Return only line hashes/positions; never persist source line text."""
    text = raw.decode("utf-8-sig", errors="replace")
    digits = re.sub(r"\D", "", accession)
    matches = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line_digits = re.sub(r"\D", "", line)
        if accession in line or (digits and digits in line_digits):
            matches.append({
                "line_number": line_number,
                "line_bytes": len(line.encode("utf-8", errors="replace")),
                "line_sha256": hashlib.sha256(line.encode("utf-8", errors="replace")).hexdigest(),
            })
    return matches


def expected_entity_ciks(case: dict) -> set[str]:
    return {normalize_cik(case.get("issuer_cik", ""))} | {
        normalize_cik(value) for value in case.get("expected_entity_ciks", [])
        if normalize_cik(value)
    }


def reconcile_case(case: dict, extra_index_rows: list[dict], raw_hits: list[dict]) -> dict:
    accession = case["accession"]
    acceptance = case.get("acceptance_datetime_et", "")
    acceptance_date = acceptance_date_from_header(acceptance)
    bulk_date = case.get("bulk_filing_date", "")
    header_date = case.get("header_filed_date", "")
    master_dates = case.get("master_filed_dates", [])
    expected = expected_entity_ciks(case)

    index_rows = []
    for idx, row in enumerate(extra_index_rows):
        index_rows.append({
            "accession": accession,
            "index_date": row.get("index_date", ""),
            "filing_date": row.get("filing_date", ""),
            "form_type": str(row.get("form_type", "")).upper(),
            "cik": normalize_cik(row.get("cik", "")),
            "filename": row.get("filename", ""),
        })
    if not index_rows and int(case.get("daily_index_hit_count", 0)):
        dates = case.get("daily_index_dates", [])
        row_dates = case.get("daily_index_filed_dates", [])
        ciks = case.get("daily_index_ciks", [])
        forms = case.get("daily_index_forms", [])
        # Phase 322 preserved parsed entity metadata but not raw index rows.
        for idx_date in dates:
            for cik in ciks:
                index_rows.append({
                    "accession": accession, "index_date": idx_date,
                    "filing_date": row_dates[0] if len(row_dates) == 1 else "",
                    "form_type": forms[0] if len(forms) == 1 else "",
                    "cik": normalize_cik(cik), "filename": "",
                })

    index_dates = sorted({row["index_date"] for row in index_rows if row["index_date"]})
    row_dates = sorted({row["filing_date"] for row in index_rows if row["filing_date"]})
    index_forms = sorted({row["form_type"] for row in index_rows if row["form_type"]})
    index_ciks = sorted({row["cik"] for row in index_rows if row["cik"]})
    owner_coverage = bool(index_rows and expected.issubset(set(index_ciks)))
    bulk_header_master_agree = bool(
        bulk_date and header_date == bulk_date and master_dates == [bulk_date]
    )
    header_acceptance_date_match = bool(acceptance_date and header_date)
    acceptance_lag = business_day_lag(header_date, acceptance_date) if header_acceptance_date_match else None
    raw_line_present = bool(raw_hits)
    raw_line_parsed = bool(index_rows)

    if len(index_dates) > 1:
        classification = "MULTIPLE_DAILY_INDEX_DATES_QUARANTINED"
    elif raw_line_present and not raw_line_parsed:
        classification = "RAW_INDEX_LINE_PRESENT_PARSER_MISS_QUARANTINED"
    elif index_rows and not bulk_header_master_agree:
        classification = "BULK_HEADER_MASTER_FILED_DATE_CONFLICT_QUARANTINED"
    elif index_rows and index_forms != [case.get("form_type", "").upper()]:
        classification = "DAILY_INDEX_FORM_CONFLICT_QUARANTINED"
    elif index_rows and not owner_coverage:
        classification = "DAILY_INDEX_ENTITY_COVERAGE_INCOMPLETE_QUARANTINED"
    elif index_rows and acceptance_date and index_dates == [acceptance_date] and row_dates == [acceptance_date]:
        if acceptance_lag is not None and acceptance_lag <= MAX_ROUTINE_ACCEPTANCE_LAG_BUSINESS_DAYS:
            classification = "FILED_DATE_ACCEPTANCE_INDEX_TWO_CLOCKS_CORROBORATED"
        else:
            classification = "LONG_ACCEPTANCE_LAG_INDEX_FOUND_QUARANTINED"
    elif index_rows:
        classification = "INDEX_ACCEPTANCE_DATE_DIVERGENCE_QUARANTINED"
    elif raw_line_present:
        classification = "RAW_INDEX_LINE_PRESENT_PARSER_MISS_QUARANTINED"
    else:
        classification = "HEADER_MASTER_CONFIRMED_DAILY_INDEX_ABSENT_QUARANTINED"

    index_date = index_dates[0] if len(index_dates) == 1 else ""
    availability_anchor = index_date if classification == "FILED_DATE_ACCEPTANCE_INDEX_TWO_CLOCKS_CORROBORATED" else ""
    return {
        "accession": accession,
        "quarter": case.get("quarter", ""),
        "form_type": case.get("form_type", ""),
        "issuer_name": case.get("issuer_name", ""),
        "ticker_as_filed": case.get("ticker_as_filed", ""),
        "bulk_filing_date": bulk_date,
        "header_filed_as_of_date": header_date,
        "master_index_filed_dates": master_dates,
        "acceptance_datetime_et": acceptance,
        "acceptance_date": acceptance_date,
        "acceptance_lag_business_days": acceptance_lag,
        "daily_index_file_dates": index_dates,
        "daily_index_row_filed_dates": row_dates,
        "daily_index_forms": index_forms,
        "daily_index_entity_ciks": index_ciks,
        "expected_entity_ciks": sorted(expected),
        "all_expected_entity_ciks_present": owner_coverage,
        "raw_daily_index_line_hits": len(raw_hits),
        "raw_daily_index_line_metadata": raw_hits,
        "parsed_daily_index_entity_rows": len(index_rows),
        "bulk_header_master_filed_date_agree": bulk_header_master_agree,
        "acceptance_date_matches_daily_index_file_date": bool(acceptance_date and index_date == acceptance_date),
        "daily_index_row_date_matches_acceptance_date": bool(acceptance_date and row_dates == [acceptance_date]),
        "availability_anchor_date": availability_anchor,
        "availability_rule": (
            "first full XNYS session strictly after the daily-index file date; "
            "this is a conservative date-level rule, not an exact first-public timestamp"
            if availability_anchor else "not admitted; unresolved daily-index evidence"
        ),
        "classification": classification,
        "strict_pit_admitted": False,
    }


def run_audit(source_dir: Path, output_dir: Path, email: str) -> dict:
    if not email.strip() or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required_no_address_inferred")
    source_path = source_dir / "phase322_exception_adjudication_result.json"
    if not source_path.is_file():
        raise FileNotFoundError("phase322_source_artifact_missing")
    source = read_source(source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    retrieval_errors, parser_errors = [], []
    new_index_manifest = {}
    new_rows_by_accession = {}
    raw_hits_by_accession = {}

    unresolved = [case for case in source["cases"] if int(case.get("daily_index_hit_count", 0)) == 0]
    date_to_unresolved = {}
    for case in unresolved:
        acceptance_date = acceptance_date_from_header(case.get("acceptance_datetime_et", ""))
        date_to_unresolved[case["accession"]] = candidate_dates_from_acceptance(acceptance_date)
    dates_to_fetch = sorted({day for days in date_to_unresolved.values() for day in days})

    for index_date in dates_to_fetch:
        url = index_url(index_date)
        try:
            raw, headers = _fetch_bytes(url, user_agent, total_bytes)
        except RetrievalError as exc:
            retrieval_errors.append({"index_date": index_date, "error": str(exc)})
            continue
        try:
            parsed = parse_daily_form_index(raw, _index_path(index_date))
            if parsed.get("index_date") != index_date:
                raise ValueError("index_filename_date_mismatch")
        except Exception as exc:
            parser_errors.append({
                "index_date": index_date,
                "error": type(exc).__name__ + ":" + str(exc)[:160],
            })
            continue
        new_index_manifest[index_date] = {
            "index_date": index_date, "url": url, "bytes": len(raw),
            "sha256": sha256_bytes(raw),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": headers.get("http_status", ""),
            "format": parsed.get("format"), "counts": parsed.get("counts", {}),
        }
        raw_text = raw.decode("utf-8-sig", errors="replace")
        for accession, candidate_days in date_to_unresolved.items():
            if index_date not in candidate_days:
                continue
            line_matches = raw_line_matches(raw, accession)
            if line_matches:
                raw_hits_by_accession.setdefault(accession, []).extend([
                    {"index_date": index_date, **item} for item in line_matches
                ])
            for row in parsed.get("records", []):
                if normalize_accession(row.get("accession", "")) == accession:
                    new_rows_by_accession.setdefault(accession, []).append({
                        **row, "index_date": index_date,
                    })

    results = []
    for case in source["cases"]:
        accession = case["accession"]
        results.append(reconcile_case(
            case,
            new_rows_by_accession.get(accession, []),
            raw_hits_by_accession.get(accession, []),
        ))

    class_counts = dict(sorted(Counter(row["classification"] for row in results).items()))
    corroborated = sum(
        row["classification"] == "FILED_DATE_ACCEPTANCE_INDEX_TWO_CLOCKS_CORROBORATED"
        for row in results
    )
    long_lag = sum(row["classification"] == "LONG_ACCEPTANCE_LAG_INDEX_FOUND_QUARANTINED" for row in results)
    unresolved_count = len(results) - corroborated
    result = {
        "phase": PHASE,
        "status": "PASS_TWO_CLOCK_RECONCILIATION_WITH_QUARANTINE" if unresolved_count else "PASS_TWO_CLOCK_RECONCILIATION_COMPLETE",
        "source_phase322": {
            "run_id": SOURCE_RUN_ID, "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_name": SOURCE_ARTIFACT_NAME, "artifact_sha256": SOURCE_ARTIFACT_SHA256,
            "exceptions_reconciled": len(results),
            "source_result_sha256": sha256_bytes(source_path.read_bytes()),
        },
        "summary": {
            "total_exceptions": len(results),
            "two_clock_cases_corroborated": corroborated,
            "long_acceptance_lag_quarantined": long_lag,
            "other_quarantined": unresolved_count - long_lag,
            "class_counts": class_counts,
            "acceptance_date_search_cases": len(unresolved),
            "acceptance_date_search_files": len(new_index_manifest),
            "raw_index_line_hits": sum(len(v) for v in raw_hits_by_accession.values()),
        },
        "two_clock_interpretation": {
            "bulk_filing_date_and_header_filed_as_of_date": "legal/as-filed date anchor",
            "acceptance_datetime": "EDGAR acceptance timestamp; not transmission commencement or exact first-public receipt",
            "daily_index_file_and_row_date": "observed SEC daily-index date; in corroborated cases it matches acceptance date",
            "conservative_availability_rule": "use the daily-index file date, not an earlier bulk/header filed-as-of date; permit strategy use no earlier than the first full XNYS session strictly after that date",
            "exact_first_public_receipt_time_verified": False,
            "strict_pit_admitted": False,
            "sample_limit": "the 24 cases are a purposive exception set, not a probability sample; do not generalize the 21-case relationship to all filings without a broader stratified audit",
        },
        "cases": results,
        "new_daily_index_manifest": list(new_index_manifest.values()),
        "retrieval": {
            "http_request_errors": len(retrieval_errors),
            "parser_errors": len(parser_errors),
            "total_sec_bytes_downloaded": total_bytes[0],
            "retrieval_errors": retrieval_errors,
            "parser_error_details": parser_errors,
            "raw_sec_bytes_uploaded": False,
        },
        "controls": {
            "strict_pit_admitted": False, "alpha_test_authorized": False,
            "return_test_run": False, "bootstrap_loo_run": False,
            "chronological_oos_run": False, "holdout_used": False,
            "f80_frozen": True, "production_changed": False,
            "universe_changed": False, "capital_changed": False,
            "parameters_changed": False, "raw_sec_bytes_uploaded": False,
            "vendor_contacted": False, "data_purchased": False, "email_sent": False,
        },
    }
    validate_result(result)
    write_csv(output_dir / "phase323_two_clock_reconciliation.csv", results)
    write_csv(output_dir / "phase323_new_daily_index_manifest.csv", list(new_index_manifest.values()))
    (output_dir / "phase323_two_clock_reconciliation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PHASE323_RESULT=" + json.dumps({
        "status": result["status"], "summary": result["summary"],
        "request_errors": len(retrieval_errors), "parser_errors": len(parser_errors),
        "bytes": total_bytes[0],
    }, sort_keys=True))
    return result


def validate_result(result: dict) -> None:
    if result.get("phase") != PHASE:
        raise ValueError("phase_number_mismatch")
    summary = result.get("summary", {})
    if summary.get("total_exceptions") != EXPECTED_EXCEPTIONS:
        raise ValueError("expected_24_exception_rows")
    if summary.get("two_clock_cases_corroborated", 0) + summary.get("long_acceptance_lag_quarantined", 0) + summary.get("other_quarantined", 0) != EXPECTED_EXCEPTIONS:
        raise ValueError("exception_denominator_mismatch")
    controls = result.get("controls", {})
    if controls.get("f80_frozen") is not True:
        raise ValueError("f80_not_frozen")
    for key in (
        "strict_pit_admitted", "alpha_test_authorized", "return_test_run",
        "bootstrap_loo_run", "chronological_oos_run", "holdout_used",
        "production_changed", "universe_changed", "capital_changed",
        "parameters_changed", "raw_sec_bytes_uploaded", "vendor_contacted",
        "data_purchased", "email_sent",
    ):
        if controls.get(key) is not False:
            raise ValueError("research_control_opened:" + key)
    if result.get("retrieval", {}).get("raw_sec_bytes_uploaded") is not False:
        raise ValueError("raw_sec_bytes_must_not_be_uploaded")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run_audit(args.source_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))


if __name__ == "__main__":
    main()
