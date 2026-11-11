"""Phase 295: real SEC daily-index and SEC-HEADER receipt-clock pilot for Form 4."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from research.phase193_nport_raw_filing_retrieval import parse_submission_header
from research.phase283_sec_daily_index_parser import (
    build_accession_ledger,
    parse_daily_form_index,
)

# First/middle/last deterministic accession samples from each of the six
# Phase 294 bulk archives. These are purposive parser/PIT controls, not a
# prevalence sample or a security-universe sample.
SAMPLE_ACCESSIONS = [
    {"quarter": "2006Q1", "accession": "0000005513-06-000002", "filing_date": "2006-01-03", "form": "4"},
    {"quarter": "2006Q1", "accession": "0001180561-06-000004", "filing_date": "2006-02-14", "form": "4"},
    {"quarter": "2006Q1", "accession": "0001358010-06-000004", "filing_date": "2006-03-31", "form": "4"},
    {"quarter": "2012Q1", "accession": "0000003545-12-000001", "filing_date": "2012-01-03", "form": "4"},
    {"quarter": "2012Q1", "accession": "0001250074-12-000001", "filing_date": "2012-02-16", "form": "4"},
    {"quarter": "2012Q1", "accession": "0001530981-12-000031", "filing_date": "2012-03-30", "form": "4"},
    {"quarter": "2023Q1", "accession": "0000009984-23-000002", "filing_date": "2023-01-03", "form": "4"},
    {"quarter": "2023Q1", "accession": "0001209191-23-011336", "filing_date": "2023-02-21", "form": "4"},
    {"quarter": "2023Q1", "accession": "0001930405-23-000004", "filing_date": "2023-03-31", "form": "4"},
    {"quarter": "2023Q2", "accession": "0000010254-23-000073", "filing_date": "2023-04-03", "form": "4"},
    {"quarter": "2023Q2", "accession": "0001225208-23-006035", "filing_date": "2023-05-18", "form": "4"},
    {"quarter": "2023Q2", "accession": "0001983686-23-000004", "filing_date": "2023-06-30", "form": "4"},
    {"quarter": "2025Q3", "accession": "0000014272-25-000117", "filing_date": "2025-07-01", "form": "4"},
    {"quarter": "2025Q3", "accession": "0001628280-25-040441", "filing_date": "2025-08-14", "form": "4"},
    {"quarter": "2025Q3", "accession": "0002078476-25-000003", "filing_date": "2025-09-30", "form": "4"},
    {"quarter": "2026Q3", "accession": "0000008947-26-000125", "filing_date": "2026-07-01", "form": "4"},
    {"quarter": "2026Q3", "accession": "0001213900-26-090366", "filing_date": "2026-08-14", "form": "4"},
    {"quarter": "2026Q3", "accession": "0002148361-26-000004", "filing_date": "2026-09-30", "form": "4"},
]
INDEX_LOOKAHEAD_CALENDAR_DAYS = 5
MAX_FILE_BYTES = 40 * 1024 * 1024
MAX_TOTAL_BYTES = 300 * 1024 * 1024
RETRIES = 4
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")


class RetrievalError(RuntimeError):
    pass


def candidate_index_dates(filing_date: str, lookahead_days: int = INDEX_LOOKAHEAD_CALENDAR_DAYS) -> list[str]:
    start = date.fromisoformat(filing_date)
    if lookahead_days < 1 or lookahead_days > 14:
        raise ValueError("lookahead_days must be between 1 and 14")
    return [(start + timedelta(days=i)).isoformat() for i in range(lookahead_days)]


def index_url(index_date: str) -> str:
    day = date.fromisoformat(index_date)
    quarter = ((day.month - 1) // 3) + 1
    return (
        f"https://www.sec.gov/Archives/edgar/daily-index/{day.year}/"
        f"QTR{quarter}/form.{day:%Y%m%d}.idx"
    )


def submission_url(accession: str) -> str:
    if not ACCESSION_RE.fullmatch(accession):
        raise ValueError("invalid_accession")
    cik = str(int(accession.split("-")[0]))
    digits = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{digits}/{accession}.txt"


def _fetch(url: str, user_agent: str) -> tuple[bytes, dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "www.sec.gov":
        raise RetrievalError("non_sec_https_url_rejected")
    request = Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "text/plain, */*",
        "Accept-Encoding": "identity",
    })
    for attempt in range(RETRIES + 1):
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read(MAX_FILE_BYTES + 1)
                if len(payload) > MAX_FILE_BYTES:
                    raise RetrievalError("file_size_limit_exceeded")
                final_host = urlparse(response.geturl()).netloc.lower()
                if final_host != "www.sec.gov":
                    raise RetrievalError("non_sec_redirect_rejected")
                headers = {
                    "http_status": str(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "date": response.headers.get("Date", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                    "content_length": response.headers.get("Content-Length", ""),
                    "final_url_host": final_host,
                }
                return payload, headers
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RetrievalError(f"http_{exc.code}") from None
        except URLError:
            if attempt < RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RetrievalError("url_error") from None
    raise RetrievalError("retry_exhausted")


def _accession_index_record(raw: bytes, index_date: str, accession: str) -> dict[str, Any]:
    parsed = parse_daily_form_index(raw, f"form.{date.fromisoformat(index_date):%Y%m%d}.idx")
    match = [x for x in parsed["records"] if x["accession"] == accession]
    return {
        "parsed": parsed,
        "matching_records": match,
        "quarantine_for_accession": [
            x for x in parsed["quarantine"] if x.get("accession") == accession
        ],
    }


def blocked_result() -> dict[str, Any]:
    return {
        "phase": 295,
        "status": "BLOCKED_MISSING_SEC_CONTACT_EMAIL",
        "email_secret_present": False,
        "sample_accessions": len(SAMPLE_ACCESSIONS),
        "raw_sec_requests": 0,
        "raw_index_files_downloaded": 0,
        "raw_submission_files_downloaded": 0,
        "acceptance_time_reconciled": False,
        "first_daily_index_sighting_observed": False,
        "first_public_timestamp_verified": False,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "production_changed": False,
        "decision": "No SEC request was made because SEC_CONTACT_EMAIL is absent or invalid.",
    }


def run_audit(email: str, output_dir: Path) -> dict[str, Any]:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        return blocked_result()

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_root = output_dir / "raw"
    index_root = raw_root / "daily-index"
    submission_root = raw_root / "submissions"
    index_root.mkdir(parents=True, exist_ok=True)
    submission_root.mkdir(parents=True, exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"

    sample_windows = {
        x["accession"]: candidate_index_dates(x["filing_date"])
        for x in SAMPLE_ACCESSIONS
    }
    all_index_dates = sorted({d for dates in sample_windows.values() for d in dates})
    index_results: dict[str, dict[str, Any]] = {}
    sightings_by_accession: dict[str, list[dict[str, Any]]] = {
        x["accession"]: [] for x in SAMPLE_ACCESSIONS
    }
    total_requests = 0
    total_bytes = 0

    for index_date in all_index_dates:
        url = index_url(index_date)
        item: dict[str, Any] = {
            "index_date": index_date,
            "url": url,
            "status": "PENDING",
            "matching_sample_accessions": [],
        }
        try:
            total_requests += 1
            payload, headers = _fetch(url, user_agent)
            total_bytes += len(payload)
            if total_bytes > MAX_TOTAL_BYTES:
                raise RetrievalError("total_download_size_limit_exceeded")
            parsed = parse_daily_form_index(payload, f"form.{date.fromisoformat(index_date):%Y%m%d}.idx")
            path = index_root / f"form.{date.fromisoformat(index_date):%Y%m%d}.idx"
            path.write_bytes(payload)
            targets = {x["accession"] for x in SAMPLE_ACCESSIONS}
            matching = [x for x in parsed["records"] if x["accession"] in targets]
            for record in matching:
                if index_date in sample_windows[record["accession"]]:
                    sightings_by_accession[record["accession"]].append(record)
                    item["matching_sample_accessions"].append(record["accession"])
            item.update({
                "status": "DOWNLOADED_AND_PARSED",
                "response_headers": headers,
                "raw_file": str(path.relative_to(output_dir)),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "form4_rows_seen": parsed["counts"]["form4_rows_seen"],
                "malformed_rows": parsed["counts"]["malformed_rows"],
                "quarantined_rows": len(parsed["quarantine"]),
            })
        except RetrievalError as exc:
            item.update({"status": "HTTP_OR_RETRIEVAL_ERROR", "error_code": str(exc)})
        except ValueError as exc:
            item.update({"status": "INDEX_PARSE_ERROR", "error_code": str(exc)[:240]})
        index_results[index_date] = item
        time.sleep(0.25)

    accession_results: list[dict[str, Any]] = []
    for sample in SAMPLE_ACCESSIONS:
        accession = sample["accession"]
        result: dict[str, Any] = dict(sample)
        sightings = sightings_by_accession[accession]
        ledger_result = build_accession_ledger(sightings)
        ledger = ledger_result["ledger"]
        result["daily_index_ledger"] = ledger[0] if ledger else None
        result["daily_index_quarantine"] = ledger_result["quarantine"]
        if ledger:
            result["index_status"] = "FIRST_DAILY_INDEX_SIGHTING_OBSERVED"
            index_row = ledger[0]
            result["daily_index_matches_bulk_identity"] = (
                index_row["form_type"] == sample["form"]
                and index_row["filing_date"] == sample["filing_date"]
                and index_row["cik"] == str(int(accession.split("-")[0]))
            )
        else:
            result["index_status"] = "NO_MATCH_IN_FIVE_CALENDAR_DAY_WINDOW"
            result["daily_index_matches_bulk_identity"] = False
        result["index_window_dates"] = sample_windows[accession]

        try:
            total_requests += 1
            payload, headers = _fetch(submission_url(accession), user_agent)
            total_bytes += len(payload)
            if total_bytes > MAX_TOTAL_BYTES:
                raise RetrievalError("total_download_size_limit_exceeded")
            header = parse_submission_header(payload, accession, sample["form"])
            expected_filed_date = sample["filing_date"].replace("-", "")
            filed_as_of = header.get("FILED AS OF DATE", "")
            header_date_matches = filed_as_of == expected_filed_date
            acceptance_date_matches = header.get("acceptance_date_matches_filed_date") == "true"
            header_ok = header_date_matches and acceptance_date_matches
            path = submission_root / f"{accession}.txt"
            path.write_bytes(payload)
            result.update({
                "submission_status": "HEADER_RECONCILED" if header_ok else "FILED_OR_ACCEPTANCE_DATE_MISMATCH",
                "submission_url": submission_url(accession),
                "submission_raw_file": str(path.relative_to(output_dir)),
                "submission_bytes": len(payload),
                "submission_sha256": hashlib.sha256(payload).hexdigest(),
                "submission_response_headers": headers,
                "submission_header": header,
                "bulk_filing_date_matches_header": header_date_matches,
                "acceptance_date_matches_filed_date": acceptance_date_matches,
            })
        except (RetrievalError, ValueError) as exc:
            result.update({"submission_status": "RETRIEVAL_OR_HEADER_ERROR", "submission_error": str(exc)[:240]})
        accession_results.append(result)
        time.sleep(0.25)

    header_pass = sum(x.get("submission_status") == "HEADER_RECONCILED" for x in accession_results)
    index_pass = sum(x.get("index_status") == "FIRST_DAILY_INDEX_SIGHTING_OBSERVED" for x in accession_results)
    index_lags = [
        int(x["daily_index_ledger"]["first_index_lag_days"])
        for x in accession_results if x.get("daily_index_ledger")
    ]
    index_parse_errors = sum(x["status"] == "INDEX_PARSE_ERROR" for x in index_results.values())
    downloaded_index_files = sum(x["status"] == "DOWNLOADED_AND_PARSED" for x in index_results.values())
    downloaded_submission_files = sum(x.get("submission_raw_file") is not None for x in accession_results)
    all_headers = header_pass == len(SAMPLE_ACCESSIONS)
    all_index = index_pass == len(SAMPLE_ACCESSIONS)
    index_identity_pass = all(
        x.get("daily_index_matches_bulk_identity") is True
        for x in accession_results if x.get("daily_index_ledger")
    )
    status = (
        "ALL_18_HEADERS_AND_DAILY_INDEX_SIGHTINGS_RECONCILED"
        if all_headers and all_index and index_parse_errors == 0
        else "PARTIAL_HEADER_OR_DAILY_INDEX_RECONCILIATION"
        if header_pass or index_pass
        else "NO_SAMPLE_RECONCILIATION"
    )
    return {
        "phase": 295,
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source": "SEC EDGAR historical daily form index and complete submission text",
        "email_secret_present": True,
        "sample_accessions": len(SAMPLE_ACCESSIONS),
        "acceptance_time_reconciled": all_headers,
        "daily_index_identity_reconciled": index_identity_pass,
        "submission_headers_reconciled": header_pass,
        "first_daily_index_sighting_observed": index_pass > 0,
        "daily_index_sightings_reconciled": index_pass,
        "daily_index_identity_matches": sum(x.get("daily_index_matches_bulk_identity") is True for x in accession_results),
        "index_files_expected": len(all_index_dates),
        "index_files_downloaded": downloaded_index_files,
        "index_parse_errors": index_parse_errors,
        "submission_files_downloaded": downloaded_submission_files,
        "raw_sec_requests": total_requests,
        "total_download_bytes": total_bytes,
        "first_index_lag_days": {
            "n": len(index_lags),
            "min": min(index_lags) if index_lags else None,
            "median": sorted(index_lags)[len(index_lags) // 2] if index_lags else None,
            "max": max(index_lags) if index_lags else None,
            "counts": {str(k): index_lags.count(k) for k in sorted(set(index_lags))},
        },
        "daily_index_files": list(index_results.values()),
        "accession_results": accession_results,
        "first_public_timestamp_verified": False,
        "acceptance_datetime_is_first_public_receipt": False,
        "daily_index_date_is_exact_first_public_timestamp": False,
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
        "raw_files_persisted_in_repository": False,
        "raw_files_staged_for_actions_artifact": bool(downloaded_index_files or downloaded_submission_files),
        "decision": "This is a purposive 18-accession receipt-clock pilot. Acceptance timestamps are reconciled from SEC-HEADER and daily index sightings are observed at date granularity. Neither field proves exact first-public receipt; no same-day or strict PIT trading use is admitted. A next-full-XNYS-session execution rule and broader stratified sample remain required.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase295_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    result = run_audit(os.environ.get("SEC_CONTACT_EMAIL", "").strip(), output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase295_form4_daily_index_pit_pilot.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
