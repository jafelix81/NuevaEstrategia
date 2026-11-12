#!/usr/bin/env python3
"""Phase 324: source-level adjudication of the three remaining SEC Form 4 clock exceptions.

Consumes immutable Phase 322/323 metadata, re-fetches the original SEC submission
headers and a narrow set of exact daily indexes, and records row-level accession,
entity, date and transaction-code evidence. Raw SEC bytes are hashed/parsed in
memory only; no raw filing or index bytes are uploaded. This is a PIT/data audit,
not a return or alpha test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from research.phase283_sec_daily_index_parser import parse_daily_form_index
from research.phase318_nport_next_business_day_clock import next_edgar_business_day
from research.phase319_sec_daily_index_live_pilot import parse_filing_header
from research.phase320_sec_bulk_daily_index_join import (
    RetrievalError, _fetch_bytes, _index_path, index_url,
    normalize_accession, normalize_cik, sha256_bytes,
)

PHASE = 324
EXPECTED_EXCEPTIONS = 3
MAX_ROUTINE_ACCEPTANCE_LAG_BUSINESS_DAYS = 5
EXPECTED_PHASE322_ARTIFACT_SHA256 = "c7eaf3cfc751e401d543bceeec20c3fe6643b09dfb8d2b0ff97df86070dca50d"
EXPECTED_PHASE323_ARTIFACT_SHA256 = "dacc9f8374e4f86cc31dbe59de5d856ee1900902ce4096b879b69127e38e66fb"
EXPECTED_PHASE322_RESULT_SHA256 = "f568d50b314dbff5828d1d78e6e3730b80a9cceb22acd4f1500a9f9b5586ebdb"
EXPECTED_PHASE323_RESULT_SHA256 = "96a999064d4aa0443b787a3fcbfe64234ec55c0e85c3c669ded6abb6f70bd588"


def parse_json_field(value):
    if isinstance(value, (list, dict)):
        return value
    if not value:
        return []
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []


def business_day_lag(start_text: str, end_text: str) -> int | None:
    if not start_text or not end_text:
        return None
    from research.phase318_nport_next_business_day_clock import is_edgar_business_day
    start, end = date.fromisoformat(start_text), date.fromisoformat(end_text)
    if end < start:
        return None
    count, current = 0, start
    while current < end:
        current = next_edgar_business_day(current)
        count += 1
    return count


def extract_xml_identity(raw: bytes) -> dict:
    text = raw.decode("latin-1", errors="replace")
    issuer = re.findall(r"<issuerCik>\s*([^<\s]+)\s*</issuerCik>", text, flags=re.I)
    owners = re.findall(r"<rptOwnerCik>\s*([^<\s]+)\s*</rptOwnerCik>", text, flags=re.I)
    codes = re.findall(r"<transactionCode>\s*([^<\s]+)\s*</transactionCode>", text, flags=re.I)
    acquired = re.findall(
        r"<transactionAcquiredDisposedCode>\s*<value>\s*([^<\s]+)\s*</value>",
        text, flags=re.I,
    )
    derivative_count = len(re.findall(r"<derivativeTransaction>", text, flags=re.I))
    non_derivative_count = len(re.findall(r"<nonDerivativeTransaction>", text, flags=re.I))
    return {
        "issuer_ciks": sorted({normalize_cik(v) for v in issuer if normalize_cik(v)}),
        "reporting_owner_ciks": sorted({normalize_cik(v) for v in owners if normalize_cik(v)}),
        "transaction_codes": sorted(set(v.strip().upper() for v in codes)),
        "acquired_disposed_codes": sorted(set(v.strip().upper() for v in acquired)),
        "non_derivative_transaction_count": non_derivative_count,
        "derivative_transaction_count": derivative_count,
    }


def transaction_code_buckets(codes: list[str]) -> list[str]:
    labels = {
        "P": "OPEN_MARKET_OR_PRIVATE_PURCHASE",
        "S": "OPEN_MARKET_OR_PRIVATE_SALE",
        "M": "EXERCISE_OR_CONVERSION_NOT_OPEN_MARKET",
        "A": "GRANT_AWARD_OR_OTHER_ACQUISITION",
        "D": "DISPOSITION_TO_ISSUER_OR_OTHER",
        "F": "TAX_WITHHOLDING_OR_PAYMENT",
        "G": "GIFT",
        "J": "OTHER",
        "K": "EQUITY_SWAP_OR_OTHER",
        "U": "TENDER_OR_OTHER",
        "W": "WILL_OR_INHERITANCE",
        "Z": "DEPOSIT_OR_WITHDRAWAL",
    }
    return sorted({labels.get(code, "UNCLASSIFIED_" + code) for code in codes})


def classify_index_evidence(rows: list[dict], header: dict, bulk_date: str, search_incomplete: bool = False) -> dict:
    index_dates = sorted({str(r.get("index_date", "")) for r in rows if r.get("index_date")})
    row_dates = sorted({str(r.get("filing_date", "")) for r in rows if r.get("filing_date")})
    forms = sorted({str(r.get("form_type", "")).upper() for r in rows if r.get("form_type")})
    ciks = sorted({normalize_cik(r.get("cik", "")) for r in rows if normalize_cik(r.get("cik", ""))})
    acceptance_date = header.get("acceptance_date", "")
    filed_date = header.get("filed_date", "") or bulk_date
    lag = business_day_lag(filed_date, acceptance_date) if filed_date and acceptance_date else None

    if search_incomplete:
        classification = "INDEX_SEARCH_INCOMPLETE_QUARANTINED"
    elif not rows:
        classification = "ORIGINAL_HEADER_CONFIRMED_DAILY_INDEX_ABSENT_IN_RECHECK_WINDOW_QUARANTINED"
    elif len(index_dates) > 1 or len(row_dates) > 1:
        classification = "MULTI_INDEX_DATE_OR_FILED_DATE_CONFLICT_QUARANTINED"
    elif forms != ["4"]:
        classification = "INDEX_FORM_CONFLICT_QUARANTINED"
    elif lag is not None and lag > MAX_ROUTINE_ACCEPTANCE_LAG_BUSINESS_DAYS:
        classification = "LONG_ACCEPTANCE_LAG_INDEX_FOUND_QUARANTINED"
    elif index_dates == [acceptance_date] and row_dates == [acceptance_date]:
        classification = "ACCEPTANCE_DATE_AND_DAILY_INDEX_CORROBORATED_DATE_LEVEL_ONLY"
    else:
        classification = "INDEX_ACCEPTANCE_DATE_DIVERGENCE_QUARANTINED"

    return {
        "index_dates": index_dates,
        "index_row_filed_dates": row_dates,
        "index_forms": forms,
        "index_entity_ciks": ciks,
        "acceptance_date": acceptance_date,
        "filed_date": filed_date,
        "acceptance_lag_business_days": lag,
        "classification": classification,
        "strict_pit_admitted": False,
    }


def candidate_index_dates(case: dict, prior: dict) -> list[str]:
    values = set()
    for field in ("bulk_filing_date", "header_filed_as_of_date", "acceptance_date"):
        value = case.get(field) or prior.get(field)
        if value:
            values.add(value)
            values.add(next_edgar_business_day(date.fromisoformat(value)).isoformat())
    for value in parse_json_field(prior.get("daily_index_file_dates", [])):
        if value:
            values.add(value)
    acceptance_date = prior.get("acceptance_date", "")
    if acceptance_date:
        current = date.fromisoformat(acceptance_date)
        for _ in range(6):
            values.add(current.isoformat())
            current = next_edgar_business_day(current)
    return sorted(values)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v
                for k, v in row.items()
            })


def load_sources(source_dir: Path):
    path = source_dir / "phase324_source_cases.json"
    if not path.is_file():
        raise FileNotFoundError("phase324_source_manifest_missing")
    raw = path.read_bytes()
    manifest = json.loads(raw)
    source = manifest.get("source", {})
    if manifest.get("phase") != PHASE:
        raise ValueError("source_manifest_phase_mismatch")
    if source.get("phase322_artifact_sha256") != EXPECTED_PHASE322_ARTIFACT_SHA256:
        raise ValueError("phase322_artifact_identity_mismatch")
    if source.get("phase323_artifact_sha256") != EXPECTED_PHASE323_ARTIFACT_SHA256:
        raise ValueError("phase323_artifact_identity_mismatch")
    if source.get("phase322_result_sha256") != EXPECTED_PHASE322_RESULT_SHA256:
        raise ValueError("phase322_result_identity_mismatch")
    if source.get("phase323_result_sha256") != EXPECTED_PHASE323_RESULT_SHA256:
        raise ValueError("phase323_result_identity_mismatch")
    if source.get("phase321_population_accessions") != 317267 or source.get("phase321_exceptions") != 24:
        raise ValueError("phase321_population_provenance_mismatch")
    if source.get("phase322_all_24_original_headers_and_master_index_hits") is not True:
        raise ValueError("phase322_exception_adjudication_provenance_mismatch")
    if source.get("phase323_two_clock_corroborated") != 21 or source.get("phase323_quarantined") != 3:
        raise ValueError("phase323_exception_provenance_mismatch")
    if manifest.get("controls", {}).get("f80_frozen") is not True:
        raise ValueError("f80_manifest_control_not_frozen")
    if manifest.get("controls", {}).get("raw_sec_bytes_included") is not False:
        raise ValueError("raw_sec_bytes_must_not_be_in_manifest")
    cases = manifest.get("cases", [])
    if len(cases) != EXPECTED_EXCEPTIONS:
        raise ValueError("source_manifest_case_denominator_mismatch")
    if len({x.get("accession") for x in cases}) != EXPECTED_EXCEPTIONS:
        raise ValueError("source_manifest_accession_uniqueness_failure")
    if any(x.get("phase323_classification") == "FILED_DATE_ACCEPTANCE_INDEX_TWO_CLOCKS_CORROBORATED" for x in cases):
        raise ValueError("already_corroborated_case_in_unresolved_manifest")
    if any(not x.get("header_cik") or not x.get("expected_entity_ciks") for x in cases):
        raise ValueError("source_manifest_identity_fields_missing")
    source_hashes = {
        "phase324_manifest_sha256": sha256_bytes(raw),
        "phase322_artifact_sha256": source["phase322_artifact_sha256"],
        "phase322_result_sha256": source["phase322_result_sha256"],
        "phase323_artifact_sha256": source["phase323_artifact_sha256"],
        "phase323_result_sha256": source["phase323_result_sha256"],
        "phase321_run_id": source["phase321_run_id"],
        "phase322_run_id": source["phase322_run_id"],
        "phase323_run_id": source["phase323_run_id"],
    }
    # The same three source cases carry both Phase 322 identity fields and
    # Phase 323 clock fields; the original 24-case denominators stay explicit.
    by_accession = {x["accession"]: x for x in cases}
    return manifest, manifest, by_accession, cases, source_hashes


def run_audit(source_dir: Path, output_dir: Path, email: str) -> dict:
    if not email.strip() or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required_no_address_inferred")
    d322, d323, phase322_by_accession, unresolved, source_hashes = load_sources(source_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    retrieval_errors, parser_errors = [], []
    filing_manifests, index_manifests = [], []
    parsed_rows_by_date = {}

    cases_out, index_rows_out = [], []
    for prior in unresolved:
        accession = normalize_accession(prior["accession"])
        source_case = phase322_by_accession.get(accession)
        if source_case is None:
            raise ValueError("phase322_case_missing:" + accession)
        path_cik = normalize_cik(source_case.get("header_cik", ""))
        if not path_cik:
            raise ValueError("original_header_path_cik_missing:" + accession)
        digits = re.sub(r"\D", "", accession)
        filing_url = (
            f"https://www.sec.gov/Archives/edgar/data/{path_cik}/"
            f"{digits}/{accession}.txt"
        )
        try:
            filing_raw, filing_headers = _fetch_bytes(filing_url, user_agent, total_bytes)
        except RetrievalError as exc:
            retrieval_errors.append({"accession": accession, "url": filing_url, "error": str(exc)})
            filing_raw = b""
            filing_headers = {}
        if not filing_raw:
            cases_out.append({
                "accession": accession, "issuer_name": prior.get("issuer_name", ""),
                "classification": "ORIGINAL_FILING_RETRIEVAL_FAILED_QUARANTINED",
                "filing_url": filing_url, "retrieval_error": True,
            })
            continue

        header = parse_filing_header(filing_raw)
        xml = extract_xml_identity(filing_raw)
        expected_entities = {
            normalize_cik(v) for v in parse_json_field(source_case.get("expected_entity_ciks", []))
            if normalize_cik(v)
        }
        xml_entities = set(xml["issuer_ciks"]) | set(xml["reporting_owner_ciks"])
        header_checks = {
            "accession_match": header.get("accession") == accession,
            "form_match": header.get("form_type") == prior.get("form_type", "").upper(),
            "header_cik_matches_phase322": header.get("cik") == path_cik,
            "filed_date_matches_phase322": header.get("filed_date") == source_case.get("header_filed_date", ""),
            "acceptance_datetime_matches_phase322": header.get("acceptance_datetime_et") == source_case.get("acceptance_datetime_et", ""),
            "xml_issuer_and_owner_ciks_match_phase322": xml_entities == expected_entities,
        }
        filing_manifests.append({
            "accession": accession, "url": filing_url,
            "bytes": len(filing_raw), "sha256": sha256_bytes(filing_raw),
            "http_status": filing_headers.get("http_status", ""),
            "content_type": filing_headers.get("content_type", ""),
            "header": header, "xml_identity": xml,
            "header_checks": header_checks,
        })

        dates = candidate_index_dates(source_case, prior)
        for index_date in dates:
            if index_date in parsed_rows_by_date:
                continue
            url = index_url(index_date)
            try:
                raw, response_headers = _fetch_bytes(url, user_agent, total_bytes)
            except RetrievalError as exc:
                retrieval_errors.append({"index_date": index_date, "url": url, "error": str(exc)})
                parsed_rows_by_date[index_date] = None
                continue
            try:
                parsed = parse_daily_form_index(raw, _index_path(index_date))
                if parsed.get("index_date") != index_date:
                    raise ValueError("index_filename_date_mismatch")
            except Exception as exc:
                parser_errors.append({"index_date": index_date, "error": type(exc).__name__ + ":" + str(exc)[:160]})
                parsed_rows_by_date[index_date] = None
                continue
            parsed_rows_by_date[index_date] = parsed
            index_manifests.append({
                "index_date": index_date, "url": url,
                "bytes": len(raw), "sha256": sha256_bytes(raw),
                "http_status": response_headers.get("http_status", ""),
                "format": parsed.get("format"), "counts": parsed.get("counts", {}),
            })

        exact_rows = []
        for index_date, parsed in parsed_rows_by_date.items():
            if parsed is None:
                continue
            for row in parsed.get("records", []):
                if normalize_accession(row.get("accession", "")) == accession:
                    item = {
                        "accession": accession,
                        "index_date": index_date,
                        "cik": normalize_cik(row.get("cik", "")),
                        "company_name": row.get("company_name", ""),
                        "form_type": row.get("form_type", ""),
                        "filing_date": row.get("filing_date", ""),
                        "filename": row.get("filename", ""),
                    }
                    match = re.search(r"(?:^|/)edgar/data/(\d+)/", item["filename"], flags=re.I)
                    item["path_cik"] = normalize_cik(match.group(1)) if match else ""
                    item["row_cik_path_match"] = bool(item["cik"] and item["path_cik"] and item["cik"] == item["path_cik"])
                    exact_rows.append(item)
                    index_rows_out.append(item)

        search_incomplete = any(parsed_rows_by_date.get(day) is None for day in dates)
        evidence = classify_index_evidence(
            exact_rows, header, prior.get("bulk_filing_date", ""),
            search_incomplete=search_incomplete,
        )
        entity_coverage = expected_entities.issubset(set(evidence["index_entity_ciks"]))
        filing_ok = all(header_checks.values())
        if not filing_ok:
            final_class = "ORIGINAL_HEADER_OR_XML_IDENTITY_MISMATCH_QUARANTINED"
        elif not all(row["row_cik_path_match"] for row in exact_rows):
            final_class = "INDEX_ROW_CIK_PATH_MISMATCH_QUARANTINED"
        elif exact_rows and not entity_coverage:
            final_class = "INDEX_ENTITY_COVERAGE_INCOMPLETE_QUARANTINED"
        else:
            final_class = evidence["classification"]

        cases_out.append({
            "accession": accession,
            "quarter": prior.get("quarter", ""),
            "form_type": prior.get("form_type", ""),
            "issuer_name": prior.get("issuer_name", ""),
            "ticker_as_filed": prior.get("ticker_as_filed", ""),
            "header_path_cik": path_cik,
            "filing_url": filing_url,
            "filing_sha256": sha256_bytes(filing_raw),
            "filing_bytes": len(filing_raw),
            "filing_header_checks": header_checks,
            "xml_identity": xml,
            "expected_entity_ciks": sorted(expected_entities),
            "xml_entities_match_expected": xml_entities == expected_entities,
            "transaction_code_buckets": transaction_code_buckets(xml["transaction_codes"]),
            "candidate_index_dates_checked": dates,
            "index_search_complete": not search_incomplete,
            "index_row_count": len(exact_rows),
            "index_rows": exact_rows,
            "index_entity_coverage_complete": entity_coverage,
            **evidence,
            "classification": final_class,
            "strict_pit_admitted": False,
        })

    class_counts = dict(sorted(Counter(r.get("classification", "") for r in cases_out).items()))
    result = {
        "phase": PHASE,
        "status": "PASS_SOURCE_LEVEL_EXCEPTION_ADJUDICATION_WITH_QUARANTINE",
        "source_hashes": source_hashes,
        "source_phase322_exception_denominator": 24,
        "source_phase323_exception_denominator": 24,
        "summary": {
            "target_exceptions": EXPECTED_EXCEPTIONS,
            "original_filings_retrieved": len(filing_manifests),
            "original_headers_identity_pass": sum(
                all(x["header_checks"].values()) for x in filing_manifests
            ),
            "daily_index_files_retrieved": len(index_manifests),
            "exact_accession_index_rows": len(index_rows_out),
            "class_counts": class_counts,
            "quarantined_cases": sum("QUARANTINED" in r.get("classification", "") for r in cases_out),
        },
        "availability_interpretation": {
            "acceptance_datetime": "not transmission commencement and not exact first-public receipt",
            "daily_index_date": "date-level public-index evidence only",
            "strict_pit_admitted": False,
            "conservative_rule": "do not use before the first full XNYS session strictly after a corroborated daily-index date",
        },
        "controls": {
            "f80_frozen": True, "strict_pit_admitted": False,
            "alpha_test_authorized": False, "return_test_run": False,
            "bootstrap_loo_run": False, "chronological_oos_run": False,
            "holdout_used": False, "production_changed": False,
            "universe_changed": False, "capital_changed": False,
            "parameters_changed": False, "raw_sec_bytes_uploaded": False,
            "vendor_contacted": False, "data_purchased": False, "email_sent": False,
        },
        "filing_manifests": filing_manifests,
        "index_manifests": index_manifests,
        "cases": cases_out,
        "index_rows": index_rows_out,
        "retrieval": {
            "http_request_errors": len(retrieval_errors),
            "parser_errors": len(parser_errors),
            "total_sec_bytes_downloaded": total_bytes[0],
            "retrieval_errors": retrieval_errors,
            "parser_error_details": parser_errors,
            "raw_sec_bytes_uploaded": False,
        },
    }
    validate_result(result)
    write_csv(output_dir / "phase324_exception_source_adjudication.csv", cases_out)
    write_csv(output_dir / "phase324_exact_daily_index_rows.csv", index_rows_out)
    write_csv(output_dir / "phase324_filing_manifest.csv", filing_manifests)
    write_csv(output_dir / "phase324_index_manifest.csv", index_manifests)
    (output_dir / "phase324_exception_source_adjudication_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PHASE324_RESULT=" + json.dumps({
        "status": result["status"], "summary": result["summary"],
        "retrieval": {k: result["retrieval"][k] for k in ("http_request_errors", "parser_errors", "total_sec_bytes_downloaded")},
    }, sort_keys=True))
    return result


def validate_result(result: dict) -> None:
    if result.get("phase") != PHASE:
        raise ValueError("phase_number_mismatch")
    summary = result.get("summary", {})
    if summary.get("target_exceptions") != EXPECTED_EXCEPTIONS:
        raise ValueError("target_exception_denominator_mismatch")
    if summary.get("original_filings_retrieved") != EXPECTED_EXCEPTIONS:
        raise ValueError("not_all_original_filings_retrieved")
    if len(result.get("cases", [])) != EXPECTED_EXCEPTIONS:
        raise ValueError("case_count_mismatch")
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
    if result.get("retrieval", {}).get("http_request_errors") != 0:
        raise ValueError("SEC_retrieval_errors_present")
    if result.get("retrieval", {}).get("parser_errors") != 0:
        raise ValueError("daily_index_parser_errors_present")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    run_audit(args.source_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))


if __name__ == "__main__":
    main()
