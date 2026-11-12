#!/usr/bin/env python3
"""Phase 321: complete six-quarter SEC Form 4/4-A bulk-to-daily-index census.

Uses the immutable Phase 294 bulk archives, downloads each unique filed-date
daily index once, joins all Form 4/4-A accessions and reporting-owner CIKs, and
validates a stratified original-header sample across owner-count regimes.
No raw SEC bytes are persisted. This is a data/PIT feasibility audit, not an
alpha or return test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from research.phase283_sec_daily_index_parser import parse_daily_form_index
from research.phase318_nport_next_business_day_clock import next_edgar_business_day
from research.phase319_sec_daily_index_live_pilot import parse_filing_header
from research.phase320_sec_bulk_daily_index_join import (
    CUTOFF_1730, MAX_TOTAL_BYTES, PRIOR_ACCESSIONS, QUARTERS, SEC_ARCHIVES,
    RetrievalError, _fetch_bytes, _index_path, _read_table_rows,
    header_identity_flags, header_path_check_type, index_url,
    normalize_accession, normalize_bulk_date, normalize_cik, sha256_bytes,
    submission_url, verify_source_archives,
)

PHASE = 321
EXPECTED_FORM_ROWS = {
    "2006Q1": 71679, "2012Q1": 63678, "2023Q1": 63844,
    "2023Q2": 51791, "2025Q3": 32127, "2026Q3": 34148,
}
EXPECTED_TOTAL_ACCESSIONS = sum(EXPECTED_FORM_ROWS.values())
OWNER_BINS = ("1", "2", "3-5", "6+")
FORM_TYPES = ("4", "4/A")


def owner_count_bin(count: int) -> str:
    if count == 1:
        return "1"
    if count == 2:
        return "2"
    if 3 <= count <= 5:
        return "3-5"
    if count >= 6:
        return "6+"
    return "0"


def select_header_samples(rows, quarters=QUARTERS, excluded=None):
    """One deterministic header case per quarter/form/owner-count bin."""
    excluded = excluded or set()
    groups = defaultdict(list)
    for row in rows:
        if row["accession"] in excluded:
            continue
        bin_name = owner_count_bin(int(row.get("reporting_owner_count", 0)))
        if bin_name in OWNER_BINS:
            groups[(row["quarter"], row["form_type"], bin_name)].append(row)
    selected, missing = [], []
    for quarter in quarters:
        for form in FORM_TYPES:
            for bin_name in OWNER_BINS:
                candidates = groups.get((quarter, form, bin_name), [])
                if not candidates:
                    missing.append({"quarter": quarter, "form_type": form,
                                    "owner_count_bin": bin_name, "available": 0})
                    continue
                chosen = min(candidates, key=lambda row: hashlib.sha256(
                    f"phase321|{quarter}|{form}|{bin_name}|{row['accession']}".encode()
                ).hexdigest())
                item = dict(chosen)
                item["owner_count_bin"] = bin_name
                selected.append(item)
    if len({row["accession"] for row in selected}) != len(selected):
        raise ValueError("duplicate_phase321_header_sample")
    return selected, missing


def evaluate_index_rows(rows, sample, observed_index_date):
    forms = sorted({str(row.get("form_type", "")).strip().upper() for row in rows})
    filed_dates = sorted({str(row.get("filing_date", "")).strip() for row in rows})
    ciks = sorted({normalize_cik(row.get("cik", "")) for row in rows if normalize_cik(row.get("cik", ""))})
    issuer = normalize_cik(sample.get("issuer_cik", ""))
    owners = {normalize_cik(v) for v in sample.get("reporting_owner_ciks", []) if normalize_cik(v)}
    expected = ({issuer} if issuer else set()) | owners
    missing_owners = sorted(owners - set(ciks))
    unexpected = sorted(set(ciks) - expected)
    return {
        "accession_found": bool(rows),
        "index_form_match": forms == [sample["form_type"]],
        "index_filing_date_match": filed_dates == [sample["filing_date"]],
        "issuer_entity_row_present": bool(issuer and issuer in ciks),
        "reporting_owner_ciks_present": owners.issubset(set(ciks)),
        "missing_reporting_owner_ciks": missing_owners,
        "unexpected_index_entity_ciks": unexpected,
        "expected_entity_cik_count": len(expected),
        "index_entity_count": len(ciks),
        "index_entity_count_matches_expected": set(ciks) == expected,
        "index_entity_ciks": ciks,
        "index_row_count": len(rows),
        "observed_index_date": observed_index_date,
        "index_lag_calendar_days": (
            (date.fromisoformat(observed_index_date) - date.fromisoformat(sample["filing_date"])).days
            if observed_index_date else None
        ),
    }


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            })


def build_bulk_population(zips):
    bulk_by_accession = {}
    dates_by_quarter = {q: set() for q in QUARTERS}
    quarter_counts = {}
    owners_by_accession = defaultdict(set)
    invalid_rows = []

    for quarter in QUARTERS:
        zf = zips[quarter]
        submission_rows = form_rows = 0
        for raw in _read_table_rows(zf, "SUBMISSION"):
            submission_rows += 1
            form = str(raw.get("DOCUMENT_TYPE", "")).strip().upper()
            if form not in FORM_TYPES:
                continue
            form_rows += 1
            accession = normalize_accession(raw.get("ACCESSION_NUMBER", ""))
            issuer_cik = normalize_cik(raw.get("ISSUERCIK", ""))
            try:
                filing_date = normalize_bulk_date(raw.get("FILING_DATE", ""))
            except ValueError:
                filing_date = ""
            if not accession or not issuer_cik or not filing_date:
                invalid_rows.append({
                    "quarter": quarter, "accession": accession, "form_type": form,
                    "issuer_cik": issuer_cik, "filing_date": filing_date,
                    "reason": "missing_or_invalid_accession_issuer_or_filing_date",
                })
                continue
            if accession in bulk_by_accession:
                raise ValueError(f"duplicate_bulk_accession_across_archives:{accession}")
            dates_by_quarter[quarter].add(filing_date)
            bulk_by_accession[accession] = {
                "quarter": quarter, "accession": accession, "form_type": form,
                "filing_date": filing_date, "issuer_cik": issuer_cik,
                "issuer_name": str(raw.get("ISSUERNAME", "")).strip(),
                "ticker_as_filed": str(raw.get("ISSUERTRADINGSYMBOL", "")).strip(),
                "period_of_report": str(raw.get("PERIOD_OF_REPORT", "")).strip(),
                "date_of_orig_sub": str(raw.get("DATE_OF_ORIG_SUB", "")).strip(),
                "aff10b5one_raw": str(raw.get("AFF10B5ONE", "")).strip() if "AFF10B5ONE" in raw else "",
                "aff10b5one_column_present": "AFF10B5ONE" in raw,
            }
        quarter_counts[quarter] = {
            "submission_rows": submission_rows, "form4_form4a_rows": form_rows,
            "distinct_filing_dates": len(dates_by_quarter[quarter]),
            "expected_form_rows": EXPECTED_FORM_ROWS[quarter],
            "source_row_count_match": form_rows == EXPECTED_FORM_ROWS[quarter],
        }

    for quarter in QUARTERS:
        quarter_accessions = {
            accession for accession, row in bulk_by_accession.items() if row["quarter"] == quarter
        }
        for raw in _read_table_rows(zips[quarter], "REPORTINGOWNER"):
            accession = normalize_accession(raw.get("ACCESSION_NUMBER", ""))
            if accession not in quarter_accessions:
                continue
            owner = normalize_cik(raw.get("RPTOWNERCIK", ""))
            if owner:
                owners_by_accession[accession].add(owner)

    owner_distribution = {q: Counter() for q in QUARTERS}
    multi_owner_by_quarter = Counter()
    for accession, row in bulk_by_accession.items():
        owners = sorted(owners_by_accession.get(accession, set()))
        row["reporting_owner_ciks"] = owners
        row["reporting_owner_count"] = len(owners)
        row["multiple_reporting_owners"] = len(owners) > 1
        row["owner_count_bin"] = owner_count_bin(len(owners))
        owner_distribution[row["quarter"]][str(len(owners))] += 1
        if len(owners) > 1:
            multi_owner_by_quarter[row["quarter"]] += 1

    quarter_summary = {
        q: {
            **quarter_counts[q],
            "multi_owner_accessions": multi_owner_by_quarter[q],
            "owner_count_distribution": dict(sorted(
                owner_distribution[q].items(), key=lambda x: int(x[0])
            )),
        }
        for q in QUARTERS
    }
    return bulk_by_accession, dates_by_quarter, {
        "quarter_summary": quarter_summary,
        "invalid_submission_rows": invalid_rows,
        "multi_owner_accessions": sum(multi_owner_by_quarter.values()),
        "owner_count_distribution": dict(sorted(
            Counter(str(row["reporting_owner_count"]) for row in bulk_by_accession.values()).items(),
            key=lambda x: int(x[0])
        )),
    }


def run_audit(artifact_dir: Path, output_dir: Path, email: str):
    if not email.strip() or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required_no_address_inferred")
    output_dir.mkdir(parents=True, exist_ok=True)
    zips, source_archives = verify_source_archives(artifact_dir)
    bulk, dates_by_quarter, bulk_meta = build_bulk_population(zips)
    if len(bulk) != EXPECTED_TOTAL_ACCESSIONS:
        raise ValueError(f"phase321_bulk_accession_count_mismatch:{len(bulk)}:{EXPECTED_TOTAL_ACCESSIONS}")
    if any(not row["source_row_count_match"] for row in bulk_meta["quarter_summary"].values()):
        raise ValueError("phase321_quarter_form_row_count_mismatch")

    date_to_accessions = defaultdict(list)
    for accession, row in bulk.items():
        date_to_accessions[row["filing_date"]].append(accession)
    unique_dates = sorted(date_to_accessions)
    if len(unique_dates) != 377:
        raise ValueError(f"phase321_unique_filing_date_count_mismatch:{len(unique_dates)}")

    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    index_cache = {}
    index_manifests = {}
    retrieval_errors = []
    parser_errors = []

    def get_index(index_date):
        if index_date in index_cache:
            return index_cache[index_date]
        try:
            raw, headers = _fetch_bytes(index_url(index_date), user_agent, total_bytes)
        except RetrievalError as exc:
            retrieval_errors.append({"index_date": index_date, "url": index_url(index_date), "error": str(exc)})
            index_cache[index_date] = None
            return None
        try:
            parsed = parse_daily_form_index(raw, _index_path(index_date))
            if parsed.get("index_date") != index_date:
                raise ValueError("index_filename_date_mismatch")
        except Exception as exc:
            parser_errors.append({
                "index_date": index_date,
                "error": type(exc).__name__ + ":" + str(exc)[:180],
            })
            index_cache[index_date] = None
            return None
        index_manifests[index_date] = {
            "index_date": index_date, "url": index_url(index_date),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": len(raw), "sha256": sha256_bytes(raw), "http": headers,
            "format": parsed.get("format"), "counts": parsed.get("counts", {}),
        }
        index_cache[index_date] = parsed
        return parsed

    index_rows_by_accession = defaultdict(list)
    observed_date_by_accession = {}
    for filing_date in unique_dates:
        parsed = get_index(filing_date)
        if parsed is None:
            continue
        for index_row in parsed.get("records", []):
            accession = normalize_accession(index_row.get("accession", ""))
            if accession in bulk and bulk[accession]["filing_date"] == filing_date:
                index_rows_by_accession[accession].append(index_row)
                observed_date_by_accession[accession] = filing_date

    missing_by_date = defaultdict(list)
    for accession, row in bulk.items():
        if not index_rows_by_accession.get(accession):
            missing_by_date[row["filing_date"]].append(accession)
    for filing_date, missing_accessions in sorted(missing_by_date.items()):
        next_date = next_edgar_business_day(date.fromisoformat(filing_date)).isoformat()
        parsed = get_index(next_date)
        if parsed is None:
            continue
        missing_set = set(missing_accessions)
        for index_row in parsed.get("records", []):
            accession = normalize_accession(index_row.get("accession", ""))
            if accession in missing_set:
                index_rows_by_accession[accession].append(index_row)
                observed_date_by_accession[accession] = next_date

    census_rows = []
    status_counts = Counter()
    quarter_form_counts = defaultdict(Counter)
    entity_count_distribution = Counter()
    missing_owner_accessions = 0
    extra_entity_accessions = 0
    multi_entity_accessions = 0

    for accession, sample in sorted(bulk.items()):
        matching = index_rows_by_accession.get(accession, [])
        observed_date = observed_date_by_accession.get(accession, "")
        if matching:
            summary = evaluate_index_rows(matching, sample, observed_date)
        else:
            summary = {
                "accession_found": False, "index_form_match": False,
                "index_filing_date_match": False, "issuer_entity_row_present": False,
                "reporting_owner_ciks_present": False,
                "missing_reporting_owner_ciks": list(sample["reporting_owner_ciks"]),
                "unexpected_index_entity_ciks": [],
                "expected_entity_cik_count": len(set(sample["reporting_owner_ciks"]) | {sample["issuer_cik"]}),
                "index_entity_count": 0, "index_entity_count_matches_expected": False,
                "index_entity_ciks": [], "index_row_count": 0,
                "observed_index_date": "", "index_lag_calendar_days": None,
            }
        if not matching:
            status = "NOT_FOUND_ON_FILED_OR_NEXT_EDGAR_BUSINESS_DAY"
        elif not summary["index_form_match"]:
            status = "INDEX_FORM_CONFLICT"
        elif not summary["index_filing_date_match"]:
            status = "INDEX_FILED_DATE_CONFLICT"
        elif not summary["issuer_entity_row_present"]:
            status = "ISSUER_CIK_MISSING_FROM_INDEX"
        elif not summary["reporting_owner_ciks_present"]:
            status = "REPORTING_OWNER_CIK_MISSING_FROM_INDEX"
        else:
            status = "MATCHED_ON_FILED_DATE" if observed_date == sample["filing_date"] else "MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY"
        status_counts[status] += 1
        quarter_form_counts[(sample["quarter"], sample["form_type"])][status] += 1
        entity_count_distribution[str(summary["index_entity_count"])] += 1
        missing_owner_accessions += not summary["reporting_owner_ciks_present"]
        extra_entity_accessions += bool(summary["unexpected_index_entity_ciks"])
        multi_entity_accessions += summary["index_entity_count"] > 1
        census_rows.append({
            **{k: sample[k] for k in (
                "quarter", "accession", "form_type", "filing_date", "issuer_cik",
                "issuer_name", "ticker_as_filed", "reporting_owner_count",
                "multiple_reporting_owners", "owner_count_bin",
            )},
            "reporting_owner_ciks": sample["reporting_owner_ciks"],
            "observed_index_date": observed_date, "index_status": status,
            "index_form_match": summary["index_form_match"],
            "index_filing_date_match": summary["index_filing_date_match"],
            "issuer_entity_row_present": summary["issuer_entity_row_present"],
            "reporting_owner_ciks_present": summary["reporting_owner_ciks_present"],
            "missing_reporting_owner_ciks": summary["missing_reporting_owner_ciks"],
            "unexpected_index_entity_ciks": summary["unexpected_index_entity_ciks"],
            "expected_entity_cik_count": summary["expected_entity_cik_count"],
            "index_entity_count": summary["index_entity_count"],
            "index_entity_count_matches_expected": summary["index_entity_count_matches_expected"],
            "index_entity_ciks": summary["index_entity_ciks"],
            "index_row_count": summary["index_row_count"],
            "index_lag_calendar_days": summary["index_lag_calendar_days"],
            "index_file_sha256": index_manifests.get(observed_date, {}).get("sha256", ""),
        })

    header_sample, missing_header_strata = select_header_samples(
        list(bulk.values()), QUARTERS, PRIOR_ACCESSIONS
    )
    header_results = []
    header_retrieval_errors = []
    header_parser_errors = []

    for item in header_sample:
        accession = item["accession"]
        matching = index_rows_by_accession.get(accession, [])
        observed_date = observed_date_by_accession.get(accession, "")
        index_ciks = sorted({
            normalize_cik(row.get("cik", "")) for row in matching
            if normalize_cik(row.get("cik", ""))
        })
        result_row = {
            "quarter": item["quarter"], "accession": accession,
            "form_type": item["form_type"], "filing_date": item["filing_date"],
            "issuer_cik": item["issuer_cik"],
            "reporting_owner_count": item["reporting_owner_count"],
            "owner_count_bin": item["owner_count_bin"],
            "reporting_owner_ciks": item["reporting_owner_ciks"],
            "observed_index_date": observed_date,
            "index_entity_count": len(index_ciks),
            "header_status": "NOT_ATTEMPTED_NO_INDEX_MATCH",
        }
        if not matching:
            header_results.append(result_row)
            continue

        candidate_urls = [submission_url(accession, item["issuer_cik"])]
        for index_row in matching:
            filename = str(index_row.get("filename", "")).strip()
            if filename:
                candidate_urls.append(urljoin(SEC_ARCHIVES, filename.lstrip("/")))
        seen_urls = set()
        selected_payload = selected_header = selected_flags = None
        selected_headers, selected_source = {}, ""
        last_error = ""

        for candidate_url in candidate_urls:
            if candidate_url in seen_urls:
                continue
            seen_urls.add(candidate_url)
            try:
                payload, response_headers = _fetch_bytes(candidate_url, user_agent, total_bytes)
            except RetrievalError as exc:
                last_error = str(exc)
                continue
            try:
                header = parse_filing_header(payload)
            except Exception as exc:
                header_parser_errors.append({
                    "accession": accession,
                    "error": type(exc).__name__ + ":" + str(exc)[:180],
                })
                continue
            flags = header_identity_flags(header, item, index_ciks)
            identity_core = (
                flags["accession_match"] and flags["form_match"] and flags["filed_date_match"]
                and flags["header_cik_in_index_entities"] and flags["issuer_cik_in_index_entities"]
                and (flags["header_cik_matches_reporting_owner"] or flags["header_cik_matches_issuer"])
            )
            if identity_core:
                selected_payload, selected_header, selected_flags = payload, header, flags
                selected_headers = response_headers
                selected_source = "issuer_cik_path" if candidate_url == candidate_urls[0] else "index_entity_path"
                break

        if selected_payload is None:
            if last_error:
                header_retrieval_errors.append({"accession": accession, "error": last_error})
            result_row["header_status"] = "HEADER_NOT_RETRIEVED_OR_IDENTITY_UNRESOLVED"
            result_row["header_error"] = last_error
            header_results.append(result_row)
            continue

        header_cik = normalize_cik(selected_header.get("cik", ""))
        path_type = header_path_check_type(header_cik, item["issuer_cik"])
        path_hash_match, path_hash, path_error = None, "", ""
        if path_type == "SAME_ISSUER_PATH":
            path_hash_match = True
            path_hash = sha256_bytes(selected_payload)
        elif path_type == "INDEPENDENT_ENTITY_PATH":
            entity_rows = [r for r in matching if normalize_cik(r.get("cik", "")) == header_cik]
            path_urls = [submission_url(accession, header_cik)]
            for entity_row in entity_rows:
                filename = str(entity_row.get("filename", "")).strip()
                if filename:
                    path_urls.append(urljoin(SEC_ARCHIVES, filename.lstrip("/")))
            for path_url in dict.fromkeys(path_urls):
                try:
                    entity_payload, _ = _fetch_bytes(path_url, user_agent, total_bytes)
                    path_hash = sha256_bytes(entity_payload)
                    path_hash_match = path_hash == sha256_bytes(selected_payload)
                    break
                except RetrievalError as exc:
                    path_error = str(exc)

        acceptance = selected_header.get("acceptance_datetime_et", "")
        acceptance_present = bool(re.fullmatch(r"\d{14}", acceptance))
        acceptance_after_cutoff = False
        if acceptance_present:
            acceptance_after_cutoff = datetime.strptime(acceptance, "%Y%m%d%H%M%S").time() >= CUTOFF_1730
        identity_match = all((
            selected_flags["accession_match"], selected_flags["form_match"],
            selected_flags["filed_date_match"], selected_flags["header_cik_in_index_entities"],
            selected_flags["issuer_cik_in_index_entities"], acceptance_present,
        )) and (selected_flags["header_cik_matches_reporting_owner"] or selected_flags["header_cik_matches_issuer"])
        result_row.update({
            "header_status": "HEADER_IDENTITY_MATCH" if identity_match else "HEADER_IDENTITY_MISMATCH",
            "header_sha256": sha256_bytes(selected_payload),
            "header_bytes": len(selected_payload),
            "header_fetch_source": selected_source,
            "header_response_http_status": selected_headers.get("http_status", ""),
            "header_cik": header_cik,
            "header_cik_role": (
                "ISSUER_AND_REPORTING_OWNER" if selected_flags["header_cik_matches_issuer"] and selected_flags["header_cik_matches_reporting_owner"]
                else "ISSUER" if selected_flags["header_cik_matches_issuer"]
                else "REPORTING_OWNER" if selected_flags["header_cik_matches_reporting_owner"]
                else "UNRESOLVED"
            ),
            "header_identity_flags": selected_flags,
            "header_entity_path_check_type": path_type,
            "header_entity_path_sha256": path_hash,
            "header_entity_path_hash_match": path_hash_match,
            "header_entity_path_error": path_error,
            "acceptance_datetime_et": acceptance,
            "acceptance_date_matches_filed_date": selected_header.get("acceptance_date") == item["filing_date"],
            "acceptance_at_or_after_1730_et": acceptance_after_cutoff,
        })
        header_results.append(result_row)

    header_checked = [
        row for row in header_results
        if row.get("header_status") in {"HEADER_IDENTITY_MATCH", "HEADER_IDENTITY_MISMATCH"}
    ]
    header_matches = sum(row["header_status"] == "HEADER_IDENTITY_MATCH" for row in header_checked)
    independent_checked = sum(
        row.get("header_entity_path_check_type") == "INDEPENDENT_ENTITY_PATH"
        and row.get("header_entity_path_hash_match") is not None for row in header_checked
    )
    independent_matches = sum(
        row.get("header_entity_path_check_type") == "INDEPENDENT_ENTITY_PATH"
        and row.get("header_entity_path_hash_match") is True for row in header_checked
    )
    same_path_checks = sum(
        row.get("header_entity_path_check_type") == "SAME_ISSUER_PATH"
        and row.get("header_entity_path_hash_match") is True for row in header_checked
    )
    path_checks_total = independent_checked + same_path_checks
    header_path_types = dict(sorted(Counter(
        row.get("header_entity_path_check_type", "") for row in header_checked
    ).items()))
    header_roles = dict(sorted(Counter(row.get("header_cik_role", "") for row in header_checked).items()))
    header_after_1730 = sum(bool(row.get("acceptance_at_or_after_1730_et")) for row in header_checked)
    header_acceptance_present = sum(bool(row.get("acceptance_datetime_et")) for row in header_checked)
    header_acceptance_date_match = sum(bool(row.get("acceptance_date_matches_filed_date")) for row in header_checked)

    join_exceptions = sum(
        count for status, count in status_counts.items()
        if status not in {"MATCHED_ON_FILED_DATE", "MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY"}
    )
    header_exceptions = len(header_results) - header_matches
    status = (
        "PASS_COMPLETE_SIX_QUARTER_BULK_INDEX_CENSUS"
        if join_exceptions == 0 and header_exceptions == 0
        and independent_checked == independent_matches
        and path_checks_total == len(header_checked)
        else "PASS_WITH_QUARANTINED_EXCEPTIONS"
    )

    quarter_join_summary = []
    for quarter in QUARTERS:
        for form in FORM_TYPES:
            counts = quarter_form_counts[(quarter, form)]
            total = sum(counts.values())
            quarter_join_summary.append({
                "quarter": quarter, "form_type": form,
                "bulk_accessions": sum(
                    1 for row in bulk.values()
                    if row["quarter"] == quarter and row["form_type"] == form
                ),
                "found_on_filed_date": counts.get("MATCHED_ON_FILED_DATE", 0),
                "found_next_business_day": counts.get("MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY", 0),
                "not_found_or_conflicted": total - counts.get("MATCHED_ON_FILED_DATE", 0) - counts.get("MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY", 0),
            })

    index_counts = [row["counts"] for row in index_manifests.values()]
    result = {
        "phase": PHASE, "status": status,
        "date_utc": datetime.now(timezone.utc).date().isoformat(),
        "source_archives": source_archives,
        "bulk_census": {
            "total_accessions": len(bulk), "expected_total_accessions": EXPECTED_TOTAL_ACCESSIONS,
            "unique_filing_dates": len(unique_dates),
            "unique_issuers": len({row["issuer_cik"] for row in bulk.values()}),
            "multi_owner_accessions": bulk_meta["multi_owner_accessions"],
            "owner_count_distribution": bulk_meta["owner_count_distribution"],
            "invalid_submission_rows": len(bulk_meta["invalid_submission_rows"]),
            "quarter_summary": bulk_meta["quarter_summary"],
            "sample_is_probability_sample": False,
        },
        "daily_index_join": {
            "unique_daily_index_files_downloaded": len(index_manifests),
            "daily_index_bytes_downloaded": sum(row["bytes"] for row in index_manifests.values()),
            "accessions_found_on_filed_date": status_counts.get("MATCHED_ON_FILED_DATE", 0),
            "accessions_found_next_business_day": status_counts.get("MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY", 0),
            "accessions_not_found_or_conflicted": join_exceptions,
            "join_status_counts": dict(sorted(status_counts.items())),
            "multi_entity_index_accessions": multi_entity_accessions,
            "missing_reporting_owner_cik_accessions": missing_owner_accessions,
            "unexpected_index_entity_accessions": extra_entity_accessions,
            "index_entity_count_distribution": dict(sorted(entity_count_distribution.items(), key=lambda x: int(x[0]))),
            "index_parser_malformed_rows": sum(c.get("malformed_rows", 0) for c in index_counts),
            "index_parser_conflicting_accessions": sum(c.get("conflicting_duplicate_accessions", 0) for c in index_counts),
            "index_parser_issuer_path_mismatches": sum(c.get("issuer_cik_path_mismatches", 0) for c in index_counts),
            "unique_filing_dates_attempted": len(unique_dates),
        },
        "original_header_sample": {
            "sampled_headers": len(header_sample),
            "expected_strata": len(QUARTERS) * len(FORM_TYPES) * len(OWNER_BINS),
            "missing_header_strata": missing_header_strata,
            "headers_downloaded": len(header_checked),
            "headers_identity_match": header_matches,
            "headers_identity_mismatch": len(header_checked) - header_matches,
            "headers_not_retrieved_or_not_checked": len(header_results) - len(header_checked),
            "acceptance_datetime_present": header_acceptance_present,
            "acceptance_date_matches_filed_date": header_acceptance_date_match,
            "acceptance_at_or_after_1730_et": header_after_1730,
            "header_cik_roles": header_roles,
            "independent_path_crosschecks_checked": independent_checked,
            "independent_path_crosschecks_verified": independent_matches,
            "independent_path_crosschecks_mismatch": independent_checked - independent_matches,
            "same_path_identity_checks": same_path_checks,
            "path_identity_checks_total": path_checks_total,
            "header_path_check_types": header_path_types,
            "header_retrieval_errors": len(header_retrieval_errors),
            "header_parser_errors": len(header_parser_errors),
        },
        "availability_interpretation": {
            "daily_index_is_exact_first_public_receipt": False,
            "acceptance_datetime_is_transmission_start": False,
            "transmission_start_observed": False,
            "strict_pit_admitted": False,
            "conservative_date_level_rule": (
                "Use the first verified SEC daily-index date for the accession as a date-level anchor only; "
                "permit strategy use no earlier than the first full XNYS session strictly after that index date. "
                "Do not substitute ACCEPTANCE-DATETIME or PERIOD_OF_REPORT for first-public availability."
            ),
        },
        "retrieval": {
            "http_request_errors": len(retrieval_errors),
            "parser_errors": len(parser_errors),
            "total_sec_bytes_downloaded": total_bytes[0],
            "max_sec_bytes_limit": MAX_TOTAL_BYTES,
            "raw_sec_bytes_uploaded": False,
            "retrieval_errors": retrieval_errors,
            "parser_error_details": parser_errors,
            "header_retrieval_errors": header_retrieval_errors,
            "header_parser_errors": header_parser_errors,
            "daily_index_manifest": list(index_manifests.values()),
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

    if bulk_meta["invalid_submission_rows"]:
        write_csv(output_dir / "phase321_invalid_bulk_rows.csv", bulk_meta["invalid_submission_rows"])
    write_csv(output_dir / "phase321_bulk_daily_index_census.csv", census_rows)
    write_csv(output_dir / "phase321_daily_index_manifest.csv", list(index_manifests.values()))
    write_csv(output_dir / "phase321_header_sample.csv", header_results)
    write_csv(output_dir / "phase321_quarter_join_summary.csv", quarter_join_summary)
    (output_dir / "phase321_bulk_daily_index_census_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("PHASE321_RESULT=" + json.dumps({
        "status": status, "bulk_accessions": len(bulk),
        "unique_filing_dates": len(unique_dates), "daily_index_files": len(index_manifests),
        "found_on_filed_date": status_counts.get("MATCHED_ON_FILED_DATE", 0),
        "found_next_business_day": status_counts.get("MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY", 0),
        "not_found_or_conflicted": join_exceptions, "headers_sampled": len(header_sample),
        "headers_identity_match": header_matches,
        "multi_owner_accessions": bulk_meta["multi_owner_accessions"],
        "request_errors": len(retrieval_errors), "parser_errors": len(parser_errors),
    }, sort_keys=True))
    for zf in zips.values():
        zf.close()
    return result


def validate_result(result):
    if result.get("phase") != PHASE:
        raise ValueError("phase_number_mismatch")
    if result.get("source_archives", {}).get("archives_verified") != 6:
        raise ValueError("six_source_archives_not_verified")
    census = result.get("bulk_census", {})
    if census.get("total_accessions") != EXPECTED_TOTAL_ACCESSIONS:
        raise ValueError("expected_317267_bulk_accessions")
    if census.get("unique_filing_dates") != 377:
        raise ValueError("expected_377_unique_filing_dates")
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
            raise ValueError(f"control_violation:{key}")


def main(argv=None):
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_audit(args.archive_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))
    validate_result(result)
    if result.get("status") == "PASS_WITH_QUARANTINED_EXCEPTIONS":
        print("PHASE321_COMPLETED_WITH_QUARANTINED_EXCEPTIONS")


if __name__ == "__main__":
    main()
