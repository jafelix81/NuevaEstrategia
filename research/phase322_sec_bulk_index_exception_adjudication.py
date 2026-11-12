#!/usr/bin/env python3
"""Phase 322: adjudicate all Phase 321 SEC bulk-to-daily-index exceptions.

Uses the immutable Phase 321 census artifact and official SEC daily/master
indexes plus complete-submission headers. It uploads parsed metadata and
hashes only; raw SEC bytes are never persisted. This is a source/PIT audit,
not an alpha or return test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from research.phase283_sec_daily_index_parser import parse_daily_form_index
from research.phase318_nport_next_business_day_clock import next_edgar_business_day
from research.phase319_sec_daily_index_live_pilot import parse_filing_header
from research.phase320_sec_bulk_daily_index_join import (
    SEC_ARCHIVES, RetrievalError, _fetch_bytes, _index_path, index_url,
    normalize_accession, normalize_cik, sha256_bytes, submission_url,
)

PHASE = 322
SOURCE_RUN_ID = 43177940904
SOURCE_ARTIFACT_ID = 13925636412
SOURCE_ARTIFACT_NAME = "phase321-sec-bulk-daily-index-full-census"
SOURCE_ARTIFACT_SHA256 = "e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c"
EXPECTED_BULK_ACCESSIONS = 317267
EXPECTED_EXCEPTION_COUNT = 24
SEARCH_BUSINESS_DAYS = 6
FORM_TYPES = {"4", "4/A"}
CUTOFF_1730 = (17, 30)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def accession_year(accession: str) -> int:
    normalized = normalize_accession(accession)
    if not normalized:
        raise ValueError("invalid_accession_for_year")
    return 2000 + int(normalized.split("-")[1])


def candidate_business_dates(start_text: str, count: int = SEARCH_BUSINESS_DAYS) -> list[str]:
    current = date.fromisoformat(start_text)
    values = [current.isoformat()]
    for _ in range(count - 1):
        current = next_edgar_business_day(current)
        values.append(current.isoformat())
    return values


def parse_master_index(raw: bytes, year: int, quarter: int) -> tuple[list[dict], int]:
    """Parse the SEC quarterly master index and retain exact Form 4/4-A rows."""
    rows = []
    data_lines = 0
    for line in raw.decode("latin-1", errors="replace").splitlines():
        parts = line.strip().split("|", 4)
        if len(parts) != 5 or parts[0].strip().upper() == "CIK":
            continue
        cik, company, form, filed_text, filename = [part.strip() for part in parts]
        if form.upper() not in FORM_TYPES:
            continue
        data_lines += 1
        basename = filename.rsplit("/", 1)[-1]
        accession = normalize_accession(basename[:-4] if basename.lower().endswith(".txt") else basename)
        if not accession:
            continue
        try:
            filed_date = date.fromisoformat(filed_text).isoformat()
        except ValueError:
            continue
        rows.append({
            "accession": accession,
            "cik": normalize_cik(cik),
            "company_name": company,
            "form_type": form.upper(),
            "filed_date": filed_date,
            "filename": filename,
            "master_year": year,
            "master_quarter": quarter,
        })
    return rows, data_lines


def expected_ciks(case: dict) -> set[str]:
    owners = case.get("reporting_owner_ciks", [])
    if isinstance(owners, str):
        owners = json.loads(owners or "[]")
    return {normalize_cik(case.get("issuer_cik", ""))} | {
        normalize_cik(value) for value in owners if normalize_cik(value)
    }


def late_acceptance_shift_is_consistent(bulk_date: str, filed_date: str, acceptance: str) -> bool:
    if not re.fullmatch(r"\d{14}", acceptance or ""):
        return False
    accepted = datetime.strptime(acceptance, "%Y%m%d%H%M%S")
    after_cutoff = (accepted.hour, accepted.minute) >= CUTOFF_1730
    if not after_cutoff or accepted.date().isoformat() != bulk_date:
        return False
    return next_edgar_business_day(accepted.date()).isoformat() == filed_date


def classify_case(case: dict, header: dict | None, master_hits: list[dict], index_hits: list[dict]) -> dict:
    accession = case["accession"]
    expected = expected_ciks(case)
    unique_master_dates = sorted({row["filed_date"] for row in master_hits})
    unique_index_dates = sorted({row["index_date"] for row in index_hits})
    index_forms = sorted({row["form_type"].upper() for row in index_hits})
    index_filed_dates = sorted({row["filing_date"] for row in index_hits})
    index_ciks = sorted({normalize_cik(row.get("cik", "")) for row in index_hits if normalize_cik(row.get("cik", ""))})
    missing_ciks = sorted(expected - set(index_ciks))
    unexpected_ciks = sorted(set(index_ciks) - expected)

    header_valid = bool(
        header
        and header.get("accession") == accession
        and header.get("form_type", "").upper() == case["form_type"].upper()
        and header.get("cik", "") in expected
        and bool(re.fullmatch(r"\d{14}", header.get("acceptance_datetime_et", "")))
    )
    header_date = header.get("filed_date", "") if header else ""
    header_acceptance = header.get("acceptance_datetime_et", "") if header else ""
    master_identity_match = bool(
        master_hits
        and all(row["accession"] == accession and row["form_type"] == case["form_type"].upper() for row in master_hits)
    )
    index_form_match = bool(index_hits and index_forms == [case["form_type"].upper()])
    index_date_internal_match = bool(index_hits and len(unique_index_dates) == 1 and index_filed_dates == unique_index_dates)
    index_owner_coverage = bool(index_hits and expected.issubset(set(index_ciks)))

    if len(unique_index_dates) > 1:
        classification = "MULTIPLE_DAILY_INDEX_DATES_QUARANTINED"
    elif index_hits and not index_form_match:
        classification = "DAILY_INDEX_FORM_CONFLICT_QUARANTINED"
    elif index_hits and not index_date_internal_match:
        classification = "DAILY_INDEX_FILED_DATE_CONFLICT_QUARANTINED"
    elif index_hits and not index_owner_coverage:
        classification = "DAILY_INDEX_ENTITY_COVERAGE_INCOMPLETE_QUARANTINED"
    elif index_hits and (not header_valid or not master_identity_match):
        classification = "DAILY_INDEX_FOUND_HEADER_OR_MASTER_UNVERIFIED"
    elif index_hits and header_date != unique_index_dates[0]:
        classification = "HEADER_DAILY_INDEX_DATE_MISMATCH_QUARANTINED"
    elif index_hits and unique_master_dates != [unique_index_dates[0]]:
        classification = "MASTER_DAILY_INDEX_DATE_MISMATCH_QUARANTINED"
    elif index_hits and header_date == case["filing_date"]:
        classification = "BULK_DATE_CONFIRMED"
    elif index_hits and late_acceptance_shift_is_consistent(case["filing_date"], unique_index_dates[0], header_acceptance):
        classification = "LATE_ACCEPTANCE_NEXT_EDGAR_DAY_CORROBORATED"
    elif index_hits:
        classification = "BULK_DATE_DIFFERS_FROM_OFFICIAL_FILED_DATE_QUARANTINED"
    elif header_valid and master_identity_match and header_date and unique_master_dates == [header_date]:
        classification = "HEADER_MASTER_FOUND_DAILY_INDEX_MISSING_QUARANTINED"
    elif header_valid and not master_hits:
        classification = "HEADER_FOUND_MASTER_AND_DAILY_INDEX_MISSING_QUARANTINED"
    elif master_identity_match and not header_valid:
        classification = "MASTER_FOUND_HEADER_AND_DAILY_INDEX_MISSING_QUARANTINED"
    else:
        classification = "NO_CORROBORATING_HEADER_MASTER_OR_DAILY_INDEX_QUARANTINED"

    return {
        "accession": accession,
        "quarter": case["quarter"],
        "form_type": case["form_type"],
        "bulk_filing_date": case["filing_date"],
        "issuer_cik": normalize_cik(case["issuer_cik"]),
        "issuer_name": case.get("issuer_name", ""),
        "ticker_as_filed": case.get("ticker_as_filed", ""),
        "reporting_owner_count": int(case.get("reporting_owner_count", 0)),
        "expected_entity_ciks": sorted(expected),
        "master_hit_count": len(master_hits),
        "master_filed_dates": unique_master_dates,
        "master_identity_match": master_identity_match,
        "header_found": bool(header),
        "header_identity_match": header_valid,
        "header_cik": header.get("cik", "") if header else "",
        "header_filed_date": header_date,
        "acceptance_datetime_et": header_acceptance,
        "acceptance_date_matches_bulk_date": bool(header_acceptance and header_acceptance[:8] == case["filing_date"].replace("-", "")),
        "acceptance_at_or_after_1730_et": bool(
            header_acceptance and re.fullmatch(r"\d{14}", header_acceptance)
            and (int(header_acceptance[8:10]), int(header_acceptance[10:12])) >= CUTOFF_1730
        ),
        "daily_index_hit_count": len(index_hits),
        "daily_index_dates": unique_index_dates,
        "daily_index_forms": index_forms,
        "daily_index_filed_dates": index_filed_dates,
        "daily_index_ciks": index_ciks,
        "missing_expected_ciks": missing_ciks,
        "unexpected_index_ciks": unexpected_ciks,
        "index_form_match": index_form_match,
        "index_date_internal_match": index_date_internal_match,
        "index_owner_coverage": index_owner_coverage,
        "late_acceptance_shift_consistent": bool(
            index_hits and header_valid and late_acceptance_shift_is_consistent(
                case["filing_date"], unique_index_dates[0], header_acceptance
            )
        ),
        "classification": classification,
        "strict_pit_admitted": False,
    }


def load_exceptions(census_csv: Path, census_json: Path) -> tuple[list[dict], dict]:
    source = json.loads(census_json.read_text(encoding="utf-8"))
    if source.get("phase") != 321 or source.get("bulk_census", {}).get("total_accessions") != EXPECTED_BULK_ACCESSIONS:
        raise ValueError("phase321_source_census_identity_mismatch")
    rows = read_csv(census_csv)
    if len(rows) != EXPECTED_BULK_ACCESSIONS:
        raise ValueError(f"phase321_census_row_count_mismatch:{len(rows)}")
    exceptions = [row for row in rows if row.get("index_status") != "MATCHED_ON_FILED_DATE"]
    if len(exceptions) != EXPECTED_EXCEPTION_COUNT:
        raise ValueError(f"phase321_exception_count_mismatch:{len(exceptions)}")
    for row in exceptions:
        row["reporting_owner_ciks"] = json.loads(row.get("reporting_owner_ciks") or "[]")
    return exceptions, source


def run_audit(census_dir: Path, output_dir: Path, email: str) -> dict:
    if not email.strip() or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required_no_address_inferred")
    census_csv = census_dir / "phase321_bulk_daily_index_census.csv"
    census_json = census_dir / "phase321_bulk_daily_index_census_result.json"
    if not census_csv.is_file() or not census_json.is_file():
        raise FileNotFoundError("phase321_census_artifact_missing")
    exceptions, source = load_exceptions(census_csv, census_json)
    output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    retrieval_errors = []
    parser_errors = []
    master_cache = {}
    master_manifest = {}
    daily_cache = {}
    daily_manifest = {}

    years_to_search = set()
    for case in exceptions:
        years_to_search.add(accession_year(case["accession"]))
        years_to_search.add(date.fromisoformat(case["filing_date"]).year)

    master_rows_by_accession = defaultdict(list)
    for year in sorted(years_to_search):
        for quarter in range(1, 5):
            url = f"{SEC_ARCHIVES}edgar/full-index/{year}/QTR{quarter}/master.idx"
            key = (year, quarter)
            try:
                raw, headers = _fetch_bytes(url, user_agent, total_bytes)
            except RetrievalError as exc:
                retrieval_errors.append({"source": "master_index", "year": year, "quarter": quarter, "error": str(exc)})
                continue
            try:
                parsed_rows, data_line_count = parse_master_index(raw, year, quarter)
            except Exception as exc:
                parser_errors.append({"source": "master_index", "year": year, "quarter": quarter,
                                      "error": type(exc).__name__ + ":" + str(exc)[:160]})
                continue
            master_cache[key] = parsed_rows
            master_manifest[key] = {
                "year": year, "quarter": quarter, "url": url,
                "bytes": len(raw), "sha256": sha256_bytes(raw),
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "http_status": headers.get("http_status", ""),
                "form4_form4a_rows": len(parsed_rows), "parsed_form4_form4a_lines": data_line_count,
            }
            for row in parsed_rows:
                master_rows_by_accession[row["accession"]].append(row)

    # Fetch original headers first. This allows the official SEC-HEADER FILED AS OF DATE
    # to add the exact daily-index date even when the bulk FILING_DATE is shifted.
    header_by_accession = {}
    header_attempts = []
    index_rows_by_accession = defaultdict(list)
    for case in exceptions:
        accession = case["accession"]
        ciks = sorted(expected_ciks(case))
        prefix_cik = normalize_cik(accession.split("-")[0])
        if prefix_cik:
            ciks.append(prefix_cik)
        candidate_urls = []
        for cik in ciks:
            try:
                candidate_urls.append(submission_url(accession, cik))
            except ValueError:
                continue
        for row in master_rows_by_accession.get(accession, []):
            candidate_urls.append(urljoin(SEC_ARCHIVES, row["filename"].lstrip("/")))
        # Keep the issuer/owner paths before the master-index filename and preserve order.
        found_headers = {}
        for url in dict.fromkeys(candidate_urls):
            try:
                payload, headers = _fetch_bytes(url, user_agent, total_bytes)
            except RetrievalError as exc:
                header_attempts.append({"accession": accession, "url": url, "status": str(exc)})
                continue
            try:
                header = parse_filing_header(payload)
            except Exception as exc:
                parser_errors.append({"source": "submission_header", "accession": accession,
                                      "error": type(exc).__name__ + ":" + str(exc)[:160]})
                continue
            if header.get("accession") != accession or header.get("form_type", "").upper() != case["form_type"].upper():
                header_attempts.append({"accession": accession, "url": url, "status": "header_accession_or_form_mismatch"})
                continue
            digest = sha256_bytes(payload)
            header_cik = normalize_cik(header.get("cik", ""))
            found_headers[digest] = {
                **header, "cik": header_cik, "sha256": digest,
                "bytes": len(payload), "url": url,
                "http_status": headers.get("http_status", ""),
                "header_cik_expected": header_cik in expected_ciks(case),
            }
        if found_headers:
            candidates = list(found_headers.values())
            candidates.sort(key=lambda h: (not h["header_cik_expected"], h.get("filed_date", ""), h["sha256"]))
            header_by_accession[accession] = candidates[0]
            for candidate in candidates:
                header_attempts.append({
                    "accession": accession, "url": candidate["url"], "status": "HEADER_MATCH",
                    "header_cik": candidate["cik"], "header_filed_date": candidate.get("filed_date", ""),
                    "header_sha256": candidate["sha256"], "header_cik_expected": candidate["header_cik_expected"],
                })

    # Build the smallest reproducible date set: bulk date + five EDGAR business days,
    # any Phase 321 observed date, the master-index date, and the original-header date.
    candidate_dates_by_accession = {}
    all_dates = set()
    for case in exceptions:
        accession = case["accession"]
        dates = set(candidate_business_dates(case["filing_date"]))
        observed = case.get("observed_index_date", "")
        if observed:
            dates.add(observed)
        for row in master_rows_by_accession.get(accession, []):
            dates.add(row["filed_date"])
        header = header_by_accession.get(accession)
        if header and header.get("filed_date"):
            dates.add(header["filed_date"])
            dates.add(next_edgar_business_day(date.fromisoformat(header["filed_date"])).isoformat())
        candidate_dates_by_accession[accession] = sorted(dates)
        all_dates.update(dates)

    for index_date in sorted(all_dates):
        url = index_url(index_date)
        try:
            raw, headers = _fetch_bytes(url, user_agent, total_bytes)
        except RetrievalError as exc:
            retrieval_errors.append({"source": "daily_index", "index_date": index_date, "error": str(exc)})
            continue
        try:
            parsed = parse_daily_form_index(raw, _index_path(index_date))
            if parsed.get("index_date") != index_date:
                raise ValueError("index_filename_date_mismatch")
        except Exception as exc:
            parser_errors.append({"source": "daily_index", "index_date": index_date,
                                  "error": type(exc).__name__ + ":" + str(exc)[:160]})
            continue
        daily_cache[index_date] = parsed
        daily_manifest[index_date] = {
            "index_date": index_date, "url": url, "bytes": len(raw),
            "sha256": sha256_bytes(raw), "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": headers.get("http_status", ""),
            "format": parsed.get("format"), "counts": parsed.get("counts", {}),
        }
        for row in parsed.get("records", []):
            accession = normalize_accession(row.get("accession", ""))
            if accession in candidate_dates_by_accession and index_date in candidate_dates_by_accession[accession]:
                index_rows_by_accession[accession].append({**row, "index_date": index_date})

    case_results = []
    for case in exceptions:
        accession = case["accession"]
        case_results.append(classify_case(
            case,
            header_by_accession.get(accession),
            master_rows_by_accession.get(accession, []),
            index_rows_by_accession.get(accession, []),
        ))

    class_counts = dict(sorted(Counter(row["classification"] for row in case_results).items()))
    fully_corroborated = sum(row["classification"] in {
        "BULK_DATE_CONFIRMED", "LATE_ACCEPTANCE_NEXT_EDGAR_DAY_CORROBORATED"
    } for row in case_results)
    unresolved = len(case_results) - fully_corroborated
    status = "PASS_EXCEPTION_ADJUDICATION_COMPLETE" if unresolved == 0 else "PASS_WITH_QUARANTINED_EXCEPTIONS"
    result = {
        "phase": PHASE,
        "status": status,
        "source_phase321": {
            "run_id": SOURCE_RUN_ID, "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_name": SOURCE_ARTIFACT_NAME, "artifact_sha256": SOURCE_ARTIFACT_SHA256,
            "bulk_accessions": EXPECTED_BULK_ACCESSIONS,
            "exceptions_adjudicated": len(exceptions),
            "census_csv_sha256": sha256_bytes(census_csv.read_bytes()),
            "census_result_sha256": sha256_bytes(census_json.read_bytes()),
        },
        "exception_summary": {
            "total": len(case_results), "fully_corroborated": fully_corroborated,
            "quarantined_or_unresolved": unresolved, "class_counts": class_counts,
            "all_cases_have_original_header": all(row["header_found"] for row in case_results),
            "all_cases_have_master_index_hit": all(row["master_hit_count"] > 0 for row in case_results),
            "all_cases_have_daily_index_hit": all(row["daily_index_hit_count"] > 0 for row in case_results),
        },
        "master_index": {
            "files_downloaded": len(master_manifest),
            "years_searched": sorted(years_to_search),
            "manifest": list(master_manifest.values()),
        },
        "daily_index": {
            "files_downloaded": len(daily_manifest),
            "unique_candidate_dates": len(all_dates),
            "manifest": list(daily_manifest.values()),
        },
        "header_retrieval": {
            "accessions_with_header": len(header_by_accession),
            "header_path_attempts": len(header_attempts),
            "header_attempts": header_attempts,
        },
        "cases": case_results,
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
    write_csv(output_dir / "phase322_exception_adjudication.csv", case_results)
    write_csv(output_dir / "phase322_master_index_manifest.csv", list(master_manifest.values()))
    write_csv(output_dir / "phase322_daily_index_manifest.csv", list(daily_manifest.values()))
    write_csv(output_dir / "phase322_header_attempts.csv", header_attempts)
    (output_dir / "phase322_exception_adjudication_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PHASE322_RESULT=" + json.dumps({
        "status": status, "exceptions": len(case_results),
        "fully_corroborated": fully_corroborated, "quarantined_or_unresolved": unresolved,
        "class_counts": class_counts, "headers": len(header_by_accession),
        "master_files": len(master_manifest), "daily_files": len(daily_manifest),
        "request_errors": len(retrieval_errors), "parser_errors": len(parser_errors),
        "bytes": total_bytes[0],
    }, sort_keys=True))
    return result


def validate_result(result: dict) -> None:
    if result.get("phase") != PHASE:
        raise ValueError("phase_number_mismatch")
    summary = result.get("exception_summary", {})
    if summary.get("total") != EXPECTED_EXCEPTION_COUNT:
        raise ValueError("expected_24_exceptions")
    if summary.get("fully_corroborated", 0) + summary.get("quarantined_or_unresolved", 0) != EXPECTED_EXCEPTION_COUNT:
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
    parser.add_argument("--census-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_audit(args.census_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))
    if result["status"] == "PASS_WITH_QUARANTINED_EXCEPTIONS":
        print("PHASE322_COMPLETED_WITH_QUARANTINED_EXCEPTIONS")


if __name__ == "__main__":
    main()
