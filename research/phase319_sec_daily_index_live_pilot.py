#!/usr/bin/env python3
"""Phase 319: live SEC daily form-index format and accession-header pilot.

Downloads only seven selected daily form indexes and at most one Form 4 plus
one Form 4/A filing per index date. Raw index/filing bytes are hashed in memory
and never uploaded; only parsed metadata and hashes enter the artifact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, time as dt_time, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from research.phase283_sec_daily_index_parser import (
    build_accession_ledger,
    parse_daily_form_index,
)

SEC_ARCHIVES = "https://www.sec.gov/Archives/"
SEC_INDEX_ROOT = "https://www.sec.gov/Archives/edgar/daily-index/"
SAMPLE_DATES = [
    "2006-01-03",
    "2012-01-03",
    "2023-01-03",
    "2023-04-03",
    "2025-07-01",
    "2026-07-01",
    "2026-11-10",
]
FORM_TYPES = ("4", "4/A")
CUTOFF_1730 = dt_time(17, 30)
CUTOFF_2200 = dt_time(22, 0)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def quarter_path(day_text: str) -> tuple[str, str, str]:
    day = datetime.strptime(day_text, "%Y-%m-%d").date()
    quarter = ((day.month - 1) // 3) + 1
    filename = f"form.{day:%Y%m%d}.idx"
    relative = f"edgar/daily-index/{day.year}/QTR{quarter}/{filename}"
    return str(day.year), f"QTR{quarter}", relative


def normalize_accession(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def parse_filing_header(raw: bytes) -> dict[str, str]:
    text = raw.decode("latin-1", errors="replace")
    def first(pattern: str) -> str:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""
    accession = normalize_accession(first(r"^\s*ACCESSION NUMBER:\s*([0-9-]+)\s*$"))
    form_type = first(r"^\s*CONFORMED SUBMISSION TYPE:\s*([^\s]+)\s*$").upper()
    cik_raw = first(r"^\s*CENTRAL INDEX KEY:\s*(\d+)\s*$")
    filed_raw = first(r"^\s*FILED AS OF DATE:\s*(\d{8})\s*$")
    acceptance = first(r"<ACCEPTANCE-DATETIME>\s*(\d{14})")
    filed_date = ""
    if filed_raw:
        filed_date = datetime.strptime(filed_raw, "%Y%m%d").date().isoformat()
    acceptance_date = ""
    acceptance_time = ""
    if acceptance:
        accepted = datetime.strptime(acceptance, "%Y%m%d%H%M%S")
        acceptance_date = accepted.date().isoformat()
        acceptance_time = accepted.time().isoformat()
    return {
        "accession": accession,
        "form_type": form_type,
        "cik": str(int(cik_raw)) if cik_raw else "",
        "filed_date": filed_date,
        "acceptance_datetime_et": acceptance,
        "acceptance_date": acceptance_date,
        "acceptance_time_et": acceptance_time,
    }


def select_sample_records(records: list[dict], index_date: str) -> list[dict]:
    selected = []
    by_form: dict[str, dict[str, dict]] = {form: {} for form in FORM_TYPES}
    for row in records:
        form = row.get("form_type")
        accession = row.get("accession")
        if form in by_form and accession:
            by_form[form].setdefault(accession, row)
    for form in FORM_TYPES:
        candidates = list(by_form[form].values())
        if candidates:
            candidates.sort(key=lambda row: hashlib.sha256(
                f"phase319|{index_date}|{form}|{row['accession']}".encode()
            ).hexdigest())
            selected.append(candidates[0])
    return selected


def fetch_bytes(url: str, user_agent: str, minimum_delay: float = 0.5) -> tuple[bytes, dict]:
    request = Request(url, headers={
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "*/*",
    })
    last_error = None
    for attempt in range(5):
        try:
            with urlopen(request, timeout=90) as response:
                raw = response.read()
                headers = {
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                    "etag": response.headers.get("ETag", ""),
                    "date": response.headers.get("Date", ""),
                    "content_length_header": response.headers.get("Content-Length", ""),
                }
            time.sleep(minimum_delay)
            return raw, headers
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise
            retry_after = exc.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** (attempt + 1)
            time.sleep(min(wait, 30))
        except URLError as exc:
            last_error = exc
            if attempt == 4:
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"SEC request failed: {last_error}")


def verify_header_against_index(row: dict, header: dict) -> dict:
    return {
        "accession_match": bool(header["accession"] and header["accession"] == row["accession"]),
        "form_type_match": bool(header["form_type"] and header["form_type"] == row["form_type"]),
        "cik_match": bool(header["cik"] and header["cik"] == row["cik"]),
        "filed_date_match": bool(header["filed_date"] and header["filed_date"] == row["filing_date"]),
        "acceptance_datetime_present": bool(header["acceptance_datetime_et"]),
    }


def run_pilot(output_dir: Path, email: str) -> dict:
    if not email.strip() or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL secret is required; no address is inferred")
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    index_manifests = []
    all_records = []
    selected_by_accession = {}

    for day_text in SAMPLE_DATES:
        year, quarter, relative = quarter_path(day_text)
        url = urljoin(SEC_ARCHIVES, relative)
        raw, headers = fetch_bytes(url, user_agent)
        parsed = parse_daily_form_index(raw, relative)
        if parsed["index_date"] != day_text:
            raise ValueError(f"index_date_filename_mismatch:{day_text}")
        manifest = {
            "index_date": day_text,
            "filename": parsed["index_filename"],
            "url": url,
            "quarter_path": f"{year}/{quarter}",
            "retrieved_at_utc": utc_now(),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "http": headers,
            "format": parsed["format"],
            "counts": parsed["counts"],
            "quarantine_reason_counts": dict(Counter(
                item.get("reason", "unknown") for item in parsed["quarantine"]
            )),
        }
        index_manifests.append(manifest)
        all_records.extend(parsed["records"])
        for row in select_sample_records(parsed["records"], day_text):
            key = f"{row['form_type']}:{row['accession']}"
            selected_by_accession.setdefault(key, row)

    ledger = build_accession_ledger(all_records)
    header_checks = []
    for key in sorted(selected_by_accession):
        row = selected_by_accession[key]
        path = row["filename"].lstrip("/")
        if path.startswith("Archives/"):
            relative = path[len("Archives/"):]
        else:
            relative = path
        filing_url = urljoin(SEC_ARCHIVES, relative)
        raw, headers = fetch_bytes(filing_url, user_agent)
        parsed_header = parse_filing_header(raw)
        matches = verify_header_against_index(row, parsed_header)
        item = {
            "accession": row["accession"],
            "form_type": row["form_type"],
            "index_date": row["index_date"],
            "index_filename": row.get("index_filename", ""),
            "index_cik": row["cik"],
            "index_filing_date": row["filing_date"],
            "index_path": row["filename"],
            "index_date_lag_days": row["index_date_lag_days"],
            "filing_url": filing_url,
            "filing_http_status": headers["http_status"],
            "filing_content_type": headers["content_type"],
            "filing_bytes": len(raw),
            "filing_sha256": hashlib.sha256(raw).hexdigest(),
            **parsed_header,
            **{f"match_{k}": v for k, v in matches.items()},
        }
        if not all(matches.values()):
            raise ValueError(f"original_header_crosscheck_failed:{key}:{matches}")
        if not parsed_header["acceptance_datetime_et"]:
            raise ValueError(f"acceptance_datetime_missing:{key}")
        accepted = datetime.strptime(parsed_header["acceptance_datetime_et"], "%Y%m%d%H%M%S")
        item["acceptance_at_or_after_1730_et"] = accepted.time() >= CUTOFF_1730
        item["acceptance_at_or_after_2200_et"] = accepted.time() >= CUTOFF_2200
        item["acceptance_time_is_transmission_start"] = False
        item["acceptance_time_is_first_public_receipt"] = False
        header_checks.append(item)

    counts_by_format = Counter(m["format"] for m in index_manifests)
    all_counts = Counter()
    quarantine_counts = Counter()
    for manifest in index_manifests:
        all_counts.update(manifest["counts"])
        quarantine_counts.update(manifest["quarantine_reason_counts"])

    forms_in_sample = Counter(x["form_type"] for x in header_checks)
    if len(index_manifests) != len(SAMPLE_DATES):
        raise ValueError("not_all_selected_daily_indexes_downloaded")
    if len(header_checks) < len(SAMPLE_DATES):
        raise ValueError(f"too_few_original_filings_crosschecked:{len(header_checks)}")
    if forms_in_sample.get("4", 0) < 5:
        raise ValueError(f"too_few_form4_headers:{forms_in_sample.get('4', 0)}")
    if forms_in_sample.get("4/A", 0) < 1:
        raise ValueError(f"no_form4a_header_crosscheck:{forms_in_sample.get('4/A', 0)}")
    if all_counts.get("issuer_cik_path_mismatches", 0) != 0:
        raise ValueError("live_index_has_cik_path_mismatches")
    if all_counts.get("index_date_before_filing_date", 0) != 0:
        raise ValueError("live_index_has_index_date_before_filing_date")
    if all_counts.get("malformed_rows", 0) != 0:
        raise ValueError("live_index_has_malformed_rows")
    if ledger["quarantine"]:
        raise ValueError("live_index_cross_date_ledger_conflicts")

    result = {
        "phase": 319,
        "status": "PASS_LIVE_SEC_DAILY_INDEX_FORMAT_AND_HEADER_PILOT",
        "sample_dates": SAMPLE_DATES,
        "daily_index_files_downloaded": len(index_manifests),
        "daily_index_total_bytes": sum(x["bytes"] for x in index_manifests),
        "daily_index_sha256_manifest": index_manifests,
        "daily_index_format_counts": dict(counts_by_format),
        "daily_index_aggregate_parse_counts": dict(all_counts),
        "daily_index_quarantine_reason_counts": dict(quarantine_counts),
        "daily_index_parsed_form4_form4a_entity_rows": len(all_records),
        "sampled_accessions": len(header_checks),
        "sampled_accession_form_counts": dict(forms_in_sample),
        "original_filing_headers_crosschecked": len(header_checks),
        "original_filing_sha256_manifest": [
            {k: x[k] for k in (
                "accession", "form_type", "filing_url", "filing_bytes",
                "filing_sha256", "acceptance_datetime_et",
            )} for x in header_checks
        ],
        "all_header_fields_match_index": True,
        "all_acceptance_datetimes_present": True,
        "transmission_start_time_observed": False,
        "exact_first_public_receipt_time_verified": False,
        "sample_is_probability_sample": False,
        "raw_index_or_filing_bytes_uploaded": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "bootstrap_loo_tested": False,
        "chronological_oos_tested": False,
        "holdout_used": False,
        "f80_frozen": True,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "vendor_contacted": False,
        "data_purchased": False,
        "email_sent": False,
        "decision": (
            "The Phase 283 parser successfully read selected raw SEC daily form indexes across 2006–2026 "
            "and every sampled original filing header reconciled to its index row. This is a live-format "
            "and path smoke test only; it does not yet join the Phase 279 bulk archive sample or prove "
            "first-public timestamps."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "phase319_daily_index_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["index_date", "filename", "url", "retrieved_at_utc", "bytes", "sha256", "format",
                  "http_status", "content_type", "last_modified", "etag", "date", "counts",
                  "quarantine_reason_counts"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for x in index_manifests:
            writer.writerow({
                **{k: x.get(k, "") for k in fields if k not in {"http_status", "content_type", "last_modified", "etag", "date", "counts", "quarantine_reason_counts"}},
                "http_status": x["http"]["http_status"],
                "content_type": x["http"]["content_type"],
                "last_modified": x["http"]["last_modified"],
                "etag": x["http"]["etag"],
                "date": x["http"]["date"],
                "counts": json.dumps(x["counts"], sort_keys=True),
                "quarantine_reason_counts": json.dumps(x["quarantine_reason_counts"], sort_keys=True),
            })
    with (output_dir / "phase319_accession_header_crosscheck.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(header_checks[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(header_checks)
    (output_dir / "phase319_live_daily_index_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = [
        "# Phase 319 — live SEC daily-index format and original-header pilot",
        "",
        "**Status:** PASS — selected raw SEC daily indexes and original filing headers reconciled.",
        "",
        f"- Daily index files downloaded: {len(index_manifests)} across 2006–2026.",
        f"- Original filing headers crosschecked: {len(header_checks)}; all accession, form, CIK, filed-date and acceptance fields matched.",
        f"- Sample forms: {dict(forms_in_sample)}.",
        f"- Daily-index formats: {dict(counts_by_format)}.",
        "",
        "This validates the live index parser and index-to-original-document path for a small deterministic smoke sample. It does not yet join the Phase 279 bulk archive accessions or estimate coverage/prevalence.",
        "",
        "The acceptance timestamp is not the transmission-start timestamp and is not an exact first-public receipt timestamp. The daily-index date remains a conservative date-level knowledge candidate only.",
        "",
        "Raw daily index and filing bytes were not uploaded; only hashes, metadata and parsed cross-checks are retained.",
        "",
        "No return, alpha, bootstrap/LOO, chronological OOS or holdout test was run. F80 and production controls remain frozen.",
        "",
    ]
    (output_dir / "PHASE319_SEC_DAILY_INDEX_LIVE_FORMAT_PILOT_2026-11-12.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("phase319_output"))
    args = parser.parse_args()
    result = run_pilot(args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
