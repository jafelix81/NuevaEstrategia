#!/usr/bin/env python3
"""Phase 320: stratified SEC Form 4/4-A bulk-to-daily-index join audit.

Reuses the immutable Phase 294 archive artifact. Downloads only selected daily
indexes and original submission headers. Raw SEC bytes are hashed in memory
and are never uploaded or committed. This is a QA/PIT feasibility audit, not
an alpha or return test.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from typing import Any

from research.phase283_sec_daily_index_parser import parse_daily_form_index
from research.phase318_nport_next_business_day_clock import next_edgar_business_day
from research.phase319_sec_daily_index_live_pilot import parse_filing_header

SOURCE_RUN_ID = 43083625013
SOURCE_ARTIFACT_ID = 13884014630
SOURCE_ARTIFACT_NAME = "phase294-sec-form4-bulk-sample-acquisition"
QUARTERS = ("2006Q1", "2012Q1", "2023Q1", "2023Q2", "2025Q3", "2026Q3")
SAMPLE_BINS = {"4": 8, "4/A": 4}
EXPECTED_ARCHIVE_SHA256 = {
    "2006Q1": "62becdadbe5eaff68f03edefe2ba2357c8bb498a1f825b697003e087cf98e6ce",
    "2012Q1": "0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357",
    "2023Q1": "0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb",
    "2023Q2": "7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb",
    "2025Q3": "9c57f272b7230500771f661bc1fe181527ed6b76a6f45d23a910c7fc7e9fcfa4",
    "2026Q3": "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3",
}
# Accessions already used by Phase 294/295 or the Phase 319 live-format pilot.
PRIOR_ACCESSIONS = {
    "0000005513-06-000002", "0001180561-06-000004", "0001358010-06-000004",
    "0000003545-12-000001", "0001250074-12-000001", "0001530981-12-000031",
    "0000009984-23-000002", "0001209191-23-011336", "0001930405-23-000004",
    "0000010254-23-000073", "0001225208-23-006035", "0001983686-23-000004",
    "0000014272-25-000117", "0001628280-25-040441", "0002078476-25-000003",
    "0000008947-26-000125", "0001213900-26-090366", "0002148361-26-000004",
    "0000905729-06-000001", "0001019687-12-000012", "0001062993-23-008335",
    "0001510281-26-000426", "0001567619-23-000073", "0001850902-25-000021",
    "0002037266-26-000004", "0001209191-06-000021", "0001225208-12-000140",
    "0001567619-25-000360", "0001628280-23-010431", "0001628280-26-046364",
    "0001662991-26-000179", "0001819395-23-000004",
}
SEC_ROOT = "https://www.sec.gov"
SEC_ARCHIVES = "https://www.sec.gov/Archives/"
MAX_FILE_BYTES = 40 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
MIN_REQUEST_DELAY_SECONDS = 0.40
RETRIES = 4
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
CUTOFF_1730 = dt_time(17, 30)


class RetrievalError(RuntimeError):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalize_cik(value: str) -> str:
    raw = re.sub(r"\D", "", str(value or ""))
    return str(int(raw)) if raw else ""


def normalize_accession(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def header_path_check_type(header_cik: str, issuer_cik: str) -> str:
    """Distinguish an independent filer/owner path check from a same-path identity."""
    header = normalize_cik(header_cik)
    issuer = normalize_cik(issuer_cik)
    if not header or not issuer:
        return "UNRESOLVED"
    return "SAME_ISSUER_PATH" if header == issuer else "INDEPENDENT_ENTITY_PATH"


def normalize_bulk_date(value: str) -> str:
    raw = str(value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return date.fromisoformat(raw).isoformat()
    match = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", raw)
    if not match:
        raise ValueError(f"invalid_bulk_filing_date:{raw}")
    day, month_text, year = match.groups()
    month = MONTHS.get(month_text.upper())
    if month is None:
        raise ValueError(f"invalid_bulk_filing_month:{raw}")
    return date(int(year), month, int(day)).isoformat()


def _member(zf: zipfile.ZipFile, table: str) -> str:
    matches = [
        name for name in zf.namelist()
        if name.rsplit("/", 1)[-1].rsplit(".", 1)[0].upper() == table
    ]
    if len(matches) != 1:
        raise ValueError(f"table_member_count:{table}:{len(matches)}")
    return matches[0]


def _read_table_rows(zf: zipfile.ZipFile, table: str):
    with zf.open(_member(zf, table), "r") as raw:
        wrapper = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        yield from csv.DictReader(wrapper, delimiter="\t")


def _sample_rank(quarter: str, form: str, accession: str) -> str:
    return hashlib.sha256(f"phase320|{quarter}|{form}|{accession}".encode()).hexdigest()


def select_form_samples(
    by_date: dict[str, list[dict[str, str]]],
    quarter: str,
    form: str,
    bins: int,
    excluded: set[str] | None = None,
) -> list[dict[str, str]]:
    """Choose one deterministic accession from each temporal bin."""
    excluded = excluded or set()
    dates = sorted(by_date)
    if len(dates) < bins:
        raise ValueError(f"insufficient_distinct_dates:{quarter}:{form}:{len(dates)}")
    selected: list[dict[str, str]] = []
    for bin_number in range(bins):
        lo = (bin_number * len(dates)) // bins
        hi = ((bin_number + 1) * len(dates)) // bins
        if hi <= lo:
            raise ValueError(f"empty_selection_bin:{quarter}:{form}:{bin_number}")
        target_index = (lo + hi - 1) // 2
        date_order = sorted(
            dates[lo:hi],
            key=lambda value: (abs(dates.index(value) - target_index), value),
        )
        chosen = None
        for filing_date in date_order:
            candidates = [
                row for row in by_date[filing_date]
                if row.get("accession") not in excluded
            ]
            if candidates:
                chosen = sorted(
                    candidates,
                    key=lambda row: _sample_rank(quarter, form, row["accession"]),
                )[0]
                break
        if chosen is None:
            raise ValueError(f"no_eligible_accession_in_bin:{quarter}:{form}:{bin_number}")
        item = dict(chosen)
        item["selection_bin"] = str(bin_number + 1)
        selected.append(item)
    if len({row["accession"] for row in selected}) != len(selected):
        raise ValueError(f"duplicate_selected_accession:{quarter}:{form}")
    return selected


def build_quarter_sample(zf: zipfile.ZipFile, quarter: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    by_form_date: dict[str, dict[str, list[dict[str, str]]]] = {
        form: defaultdict(list) for form in SAMPLE_BINS
    }
    submission_rows = 0
    form_rows = 0
    invalid_rows = 0
    seen_accessions: set[str] = set()
    for raw in _read_table_rows(zf, "SUBMISSION"):
        submission_rows += 1
        form = str(raw.get("DOCUMENT_TYPE", "")).strip().upper()
        if form not in SAMPLE_BINS:
            continue
        form_rows += 1
        accession = normalize_accession(raw.get("ACCESSION_NUMBER", ""))
        issuer_cik = normalize_cik(raw.get("ISSUERCIK", ""))
        try:
            filing_date = normalize_bulk_date(raw.get("FILING_DATE", ""))
        except ValueError:
            filing_date = ""
        if not accession or not issuer_cik or not filing_date:
            invalid_rows += 1
            continue
        if accession in seen_accessions:
            raise ValueError(f"duplicate_submission_accession:{quarter}:{accession}")
        seen_accessions.add(accession)
        by_form_date[form][filing_date].append({
            "quarter": quarter,
            "accession": accession,
            "form_type": form,
            "filing_date": filing_date,
            "issuer_cik": issuer_cik,
            "issuer_name": str(raw.get("ISSUERNAME", "")).strip(),
            "ticker_as_filed": str(raw.get("ISSUERTRADINGSYMBOL", "")).strip(),
            "period_of_report": str(raw.get("PERIOD_OF_REPORT", "")).strip(),
            "date_of_orig_sub": str(raw.get("DATE_OF_ORIG_SUB", "")).strip(),
            "aff10b5one_raw": str(raw.get("AFF10B5ONE", "")).strip() if "AFF10B5ONE" in raw else "",
            "aff10b5one_column_present": str("AFF10B5ONE" in raw).lower(),
        })
    if invalid_rows:
        raise ValueError(f"invalid_form4_submission_rows:{quarter}:{invalid_rows}")
    selected = []
    for form, bins in SAMPLE_BINS.items():
        selected.extend(select_form_samples(
            by_form_date[form], quarter, form, bins, PRIOR_ACCESSIONS
        ))
    if len(selected) != sum(SAMPLE_BINS.values()):
        raise ValueError(f"sample_size_mismatch:{quarter}:{len(selected)}")
    return selected, {
        "submission_rows": submission_rows,
        "form4_and_4a_rows": form_rows,
        "distinct_form4_dates": {form: len(by_form_date[form]) for form in SAMPLE_BINS},
        "sampled": len(selected),
        "sampled_by_form": dict(Counter(row["form_type"] for row in selected)),
        "sampled_distinct_filing_dates": len({row["filing_date"] for row in selected}),
    }


def reporting_owner_ciks_by_accession(zf: zipfile.ZipFile, sample_accessions: set[str]) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for row in _read_table_rows(zf, "REPORTINGOWNER"):
        accession = normalize_accession(row.get("ACCESSION_NUMBER", ""))
        if accession in sample_accessions:
            owner = normalize_cik(row.get("RPTOWNERCIK", ""))
            if owner:
                owners[accession].add(owner)
    return owners


def verify_source_archives(artifact_dir: Path) -> tuple[dict[str, zipfile.ZipFile], dict[str, Any]]:
    manifest_path = artifact_dir / "phase294_form4_bulk_sample_audit.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("phase294_manifest_missing")
    source = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source.get("phase") != 294 or source.get("status") != "SIX_ARCHIVES_RAW_RETRIEVED_SCHEMA_PASS":
        raise ValueError("phase294_source_artifact_not_pass")
    if source.get("archive_bytes_sha256_verified") is not True:
        raise ValueError("phase294_source_hash_gate_not_pass")
    archive_results = {row["quarter"]: row for row in source.get("archive_results", [])}
    if set(archive_results) != set(QUARTERS):
        raise ValueError("phase294_archive_quarter_inventory_mismatch")
    zips: dict[str, zipfile.ZipFile] = {}
    verified = {}
    for quarter in QUARTERS:
        relative = f"raw/{quarter.lower()}_form345.zip"
        path = artifact_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"phase294_archive_missing:{quarter}")
        payload = path.read_bytes()
        digest = sha256_bytes(payload)
        expected = EXPECTED_ARCHIVE_SHA256[quarter]
        if digest != expected or archive_results[quarter].get("zip_sha256") != expected:
            raise ValueError(f"phase294_archive_hash_mismatch:{quarter}")
        zf = zipfile.ZipFile(io.BytesIO(payload))
        bad_member = zf.testzip()
        if bad_member:
            raise ValueError(f"phase294_zip_crc_failure:{quarter}:{bad_member}")
        for table in ("SUBMISSION", "REPORTINGOWNER"):
            _member(zf, table)
        zips[quarter] = zf
        verified[quarter] = {
            "archive_path": relative,
            "zip_bytes": len(payload),
            "sha256": digest,
            "crc_pass": True,
            "manifest_hash_match": True,
        }
    return zips, {
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_name": SOURCE_ARTIFACT_NAME,
        "source_manifest_status": source.get("status"),
        "archives_verified": len(verified),
        "archives": verified,
    }


def index_url(index_date: str) -> str:
    day = date.fromisoformat(index_date)
    quarter = ((day.month - 1) // 3) + 1
    return (
        f"{SEC_ROOT}/Archives/edgar/daily-index/{day.year}/"
        f"QTR{quarter}/form.{day:%Y%m%d}.idx"
    )


def submission_url(accession: str, issuer_cik: str) -> str:
    if not ACCESSION_RE.fullmatch(accession):
        raise ValueError("invalid_accession")
    cik = normalize_cik(issuer_cik)
    if not cik:
        raise ValueError("invalid_issuer_cik")
    return f"{SEC_ARCHIVES}edgar/data/{cik}/{accession}.txt"


def _fetch_bytes(
    url: str,
    user_agent: str,
    total_bytes: list[int],
) -> tuple[bytes, dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "www.sec.gov":
        raise RetrievalError("non_sec_https_url_rejected")
    request = Request(url, headers={
        "User-Agent": user_agent,
        "Accept-Encoding": "identity",
        "Accept": "text/plain, */*",
    })
    for attempt in range(RETRIES + 1):
        try:
            with urlopen(request, timeout=90) as response:
                payload = response.read(MAX_FILE_BYTES + 1)
                if len(payload) > MAX_FILE_BYTES:
                    raise RetrievalError("response_size_limit_exceeded")
                headers = {
                    "http_status": str(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_encoding": response.headers.get("Content-Encoding", ""),
                    "date": response.headers.get("Date", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                    "etag": response.headers.get("ETag", ""),
                    "content_length": response.headers.get("Content-Length", ""),
                }
            total_bytes[0] += len(payload)
            if total_bytes[0] > MAX_TOTAL_BYTES:
                raise RetrievalError("total_download_size_limit_exceeded")
            time.sleep(MIN_REQUEST_DELAY_SECONDS)
            return payload, headers
        except HTTPError as exc:
            if exc.code in {429, 500, 502, 503, 504} and attempt < RETRIES:
                retry_after = exc.headers.get("Retry-After", "")
                wait = float(retry_after) if retry_after.isdigit() else min(2 ** attempt, 16)
                time.sleep(min(wait, 30))
                continue
            raise RetrievalError(f"http_{exc.code}") from None
        except URLError:
            if attempt < RETRIES:
                time.sleep(min(2 ** attempt, 16))
                continue
            raise RetrievalError("url_error") from None
    raise RetrievalError("retry_exhausted")


def _index_path(index_date: str) -> str:
    day = date.fromisoformat(index_date)
    quarter = ((day.month - 1) // 3) + 1
    return f"edgar/daily-index/{day.year}/QTR{quarter}/form.{day:%Y%m%d}.idx"


def index_row_summary(
    rows: list[dict[str, Any]],
    sample: dict[str, str],
    index_date: str,
) -> dict[str, Any]:
    forms = sorted({str(row.get("form_type", "")) for row in rows})
    filed_dates = sorted({str(row.get("filing_date", "")) for row in rows})
    ciks = sorted({normalize_cik(row.get("cik", "")) for row in rows})
    issuer_cik = normalize_cik(sample["issuer_cik"])
    return {
        "accession_found": bool(rows),
        "index_form_match": forms == [sample["form_type"]],
        "index_filing_date_match": filed_dates == [sample["filing_date"]],
        "issuer_entity_row_present": issuer_cik in ciks,
        "index_entity_count": len(ciks),
        "index_entity_ciks": ciks,
        "index_row_count": len(rows),
        "observed_index_date": index_date,
        "index_lag_calendar_days": (date.fromisoformat(index_date) - date.fromisoformat(sample["filing_date"])).days,
    }


def header_identity_flags(
    header: dict[str, str],
    sample: dict[str, str],
    index_entity_ciks: list[str],
) -> dict[str, bool]:
    header_cik = normalize_cik(header.get("cik", ""))
    issuer_cik = normalize_cik(sample.get("issuer_cik", ""))
    owner_ciks = {normalize_cik(value) for value in sample.get("reporting_owner_ciks", [])}
    index_ciks = {normalize_cik(value) for value in index_entity_ciks}
    return {
        "accession_match": header.get("accession") == sample["accession"],
        "form_match": header.get("form_type", "").upper() == sample["form_type"],
        "filed_date_match": header.get("filed_date") == sample["filing_date"],
        "header_cik_in_index_entities": bool(header_cik and header_cik in index_ciks),
        "issuer_cik_in_index_entities": bool(issuer_cik and issuer_cik in index_ciks),
        "header_cik_matches_reporting_owner": bool(header_cik and header_cik in owner_ciks),
        "header_cik_matches_issuer": bool(header_cik and header_cik == issuer_cik),
        "acceptance_datetime_present": bool(re.fullmatch(r"\d{14}", header.get("acceptance_datetime_et", ""))),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            cooked = {}
            for key, value in row.items():
                cooked[key] = json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
            writer.writerow(cooked)


def validate_result(result: dict[str, Any]) -> None:
    if result.get("phase") != 320:
        raise ValueError("phase_number_mismatch")
    if result.get("source_archives", {}).get("archives_verified") != 6:
        raise ValueError("six_source_archives_not_verified")
    if result.get("sample", {}).get("sampled_accessions") != 72:
        raise ValueError("expected_72_sampled_accessions")
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


def run_audit(artifact_dir: Path, output_dir: Path, email: str) -> dict[str, Any]:
    if not email.strip() or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required_no_address_inferred")
    output_dir.mkdir(parents=True, exist_ok=True)
    zips, source_archives = verify_source_archives(artifact_dir)

    sample: list[dict[str, str]] = []
    quarter_summary = {}
    for quarter in QUARTERS:
        rows, summary = build_quarter_sample(zips[quarter], quarter)
        sample.extend(rows)
        quarter_summary[quarter] = summary
    if len(sample) != 72 or len({row["accession"] for row in sample}) != 72:
        raise ValueError("global_sample_accession_count_or_uniqueness_failure")

    sample_accessions = {row["accession"] for row in sample}
    owner_ciks_by_acc: dict[str, set[str]] = {}
    for quarter in QUARTERS:
        quarter_accessions = {row["accession"] for row in sample if row["quarter"] == quarter}
        owner_ciks_by_acc.update(reporting_owner_ciks_by_accession(zips[quarter], quarter_accessions))
    for row in sample:
        row["reporting_owner_ciks"] = sorted(owner_ciks_by_acc.get(row["accession"], set()))
        row["reporting_owner_count"] = len(row["reporting_owner_ciks"])
        row["multiple_reporting_owners"] = row["reporting_owner_count"] > 1

    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    total_bytes = [0]
    index_cache: dict[str, dict[str, Any]] = {}
    index_manifests: dict[str, dict[str, Any]] = {}
    sample_results = []
    retrieval_errors = []
    parser_errors = []

    def get_index(index_date: str) -> dict[str, Any]:
        if index_date in index_cache:
            return index_cache[index_date]
        url = index_url(index_date)
        raw, headers = _fetch_bytes(url, user_agent, total_bytes)
        parsed = parse_daily_form_index(raw, _index_path(index_date))
        if parsed.get("index_date") != index_date:
            raise ValueError(f"index_filename_date_mismatch:{index_date}")
        counts = parsed.get("counts", {})
        if counts.get("malformed_rows", 0) or counts.get("conflicting_duplicate_accessions", 0):
            parser_errors.append({
                "index_date": index_date,
                "malformed_rows": counts.get("malformed_rows", 0),
                "conflicting_duplicate_accessions": counts.get("conflicting_duplicate_accessions", 0),
            })
        index_manifests[index_date] = {
            "index_date": index_date,
            "url": url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": len(raw),
            "sha256": sha256_bytes(raw),
            "http": headers,
            "format": parsed.get("format"),
            "counts": counts,
        }
        index_cache[index_date] = parsed
        return parsed

    for item in sample:
        row_result = dict(item)
        row_result["expected_index_date"] = item["filing_date"]
        parsed = None
        chosen_date = item["filing_date"]
        try:
            parsed = get_index(chosen_date)
        except RetrievalError as exc:
            retrieval_errors.append({
                "accession": item["accession"],
                "index_date": chosen_date,
                "stage": "filed_date_index",
                "error": str(exc),
            })
            row_result["index_retrieval_error"] = str(exc)
            sample_results.append(row_result)
            continue
        matching = [
            row for row in parsed["records"]
            if row.get("accession") == item["accession"]
        ]
        if not matching:
            next_date = next_edgar_business_day(date.fromisoformat(item["filing_date"])).isoformat()
            chosen_date = next_date
            try:
                parsed = get_index(chosen_date)
            except RetrievalError as exc:
                retrieval_errors.append({
                    "accession": item["accession"],
                    "index_date": chosen_date,
                    "stage": "next_business_day_index",
                    "error": str(exc),
                })
                row_result["index_retrieval_error"] = str(exc)
                sample_results.append(row_result)
                continue
            matching = [
                row for row in parsed["records"]
                if row.get("accession") == item["accession"]
            ]
        summary = index_row_summary(matching, item, chosen_date)
        row_result.update({
            "index_accession_found": summary["accession_found"],
            "index_form_match": summary["index_form_match"],
            "index_filing_date_match": summary["index_filing_date_match"],
            "issuer_entity_row_present": summary["issuer_entity_row_present"],
            "index_entity_count": summary["index_entity_count"],
            "index_entity_ciks": summary["index_entity_ciks"],
            "index_row_count": summary["index_row_count"],
            "observed_index_date": summary["observed_index_date"],
            "index_lag_calendar_days": summary["index_lag_calendar_days"],
            "index_match_on_bulk_filing_date": chosen_date == item["filing_date"] and summary["accession_found"],
        })
        if not matching:
            row_result["index_status"] = "NOT_FOUND_ON_FILED_OR_NEXT_EDGAR_BUSINESS_DAY"
            sample_results.append(row_result)
            continue
        row_result["index_status"] = (
            "MATCHED_ON_FILED_DATE" if chosen_date == item["filing_date"]
            else "MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY"
        )
        if not summary["index_form_match"] or not summary["index_filing_date_match"]:
            row_result["index_status"] = "INDEX_IDENTITY_CONFLICT"
        # Fetch the canonical issuer path first. If the SEC does not resolve it,
        # try observed index entity paths, but still require the header issuer CIK.
        header_payload = None
        header_headers = None
        fetch_source = "issuer_cik_path"
        candidate_urls = [submission_url(item["accession"], item["issuer_cik"])]
        for entity in matching:
            candidate_urls.append(urljoin(SEC_ARCHIVES, str(entity.get("filename", "")).lstrip("/")))
        seen_urls = set()
        header_error = ""
        for candidate_url in candidate_urls:
            if candidate_url in seen_urls:
                continue
            seen_urls.add(candidate_url)
            try:
                header_payload, header_headers = _fetch_bytes(candidate_url, user_agent, total_bytes)
                if candidate_url != candidate_urls[0]:
                    fetch_source = "index_entity_path_fallback"
                break
            except RetrievalError as exc:
                header_error = str(exc)
                if not header_error.endswith("http_404"):
                    break
        if header_payload is None:
            retrieval_errors.append({
                "accession": item["accession"],
                "stage": "original_submission_header",
                "error": header_error or "submission_header_not_retrieved",
            })
            row_result["header_retrieval_error"] = header_error or "submission_header_not_retrieved"
            sample_results.append(row_result)
            continue
        try:
            header = parse_filing_header(header_payload)
        except Exception as exc:
            row_result["header_parse_error"] = type(exc).__name__ + ":" + str(exc)[:180]
            parser_errors.append({
                "accession": item["accession"],
                "stage": "original_submission_header",
                "error": row_result["header_parse_error"],
            })
            sample_results.append(row_result)
            continue
        flags = header_identity_flags(header, item, summary["index_entity_ciks"])
        acceptance = header.get("acceptance_datetime_et", "")
        acceptance_after_cutoff = False
        if re.fullmatch(r"\d{14}", acceptance):
            acceptance_after_cutoff = datetime.strptime(acceptance, "%Y%m%d%H%M%S").time() >= CUTOFF_1730
        header_cik = normalize_cik(header.get("cik", ""))
        issuer_cik = normalize_cik(item["issuer_cik"])
        header_cik_role = (
            "ISSUER_AND_REPORTING_OWNER" if flags["header_cik_matches_issuer"] and flags["header_cik_matches_reporting_owner"]
            else "ISSUER" if flags["header_cik_matches_issuer"]
            else "REPORTING_OWNER" if flags["header_cik_matches_reporting_owner"]
            else "OTHER_INDEX_ENTITY" if flags["header_cik_in_index_entities"]
            else "UNRESOLVED"
        )
        path_check_type = header_path_check_type(header_cik, issuer_cik)
        # The SEC-HEADER CENTRAL INDEX KEY is the filing entity CIK; it is not
        # assumed to equal the issuer CIK in the flattened SEC bulk SUBMISSION table.
        # Verify both CIKs against the daily-index entity rows and owner table.
        header_entity_path_hash_match = None
        header_entity_path_sha256 = ""
        header_entity_path_error = ""
        if header_cik and header_cik == issuer_cik:
            header_entity_path_hash_match = True
            header_entity_path_sha256 = sha256_bytes(header_payload)
        else:
            header_entity_row = next(
                (entity for entity in matching if normalize_cik(entity.get("cik", "")) == header_cik),
                None,
            )
            if header_entity_row is None:
                header_entity_path_hash_match = False
                header_entity_path_error = "header_cik_not_present_in_index_rows"
            else:
                entity_url = urljoin(SEC_ARCHIVES, str(header_entity_row.get("filename", "")).lstrip("/"))
                try:
                    entity_payload, _entity_headers = _fetch_bytes(entity_url, user_agent, total_bytes)
                    header_entity_path_sha256 = sha256_bytes(entity_payload)
                    header_entity_path_hash_match = header_entity_path_sha256 == sha256_bytes(header_payload)
                except RetrievalError as exc:
                    header_entity_path_error = str(exc)
                    retrieval_errors.append({
                        "accession": item["accession"],
                        "stage": "header_entity_path_hash_crosscheck",
                        "error": str(exc),
                    })
        row_result.update({
            "header_sha256": sha256_bytes(header_payload),
            "header_bytes": len(header_payload),
            "header_fetch_source": fetch_source,
            "header_cik": header_cik,
            "header_cik_role": header_cik_role,
            "header_entity_path_check_type": path_check_type,
            "header_cik_equals_issuer_cik": header_cik == issuer_cik,
            "header_identity_flags": flags,
            "header_identity_match": all(flags[key] for key in (
                "accession_match", "form_match", "filed_date_match",
                "header_cik_in_index_entities", "issuer_cik_in_index_entities",
                "acceptance_datetime_present",
            )) and (flags["header_cik_matches_reporting_owner"] or flags["header_cik_matches_issuer"]),
            "header_entity_path_sha256": header_entity_path_sha256,
            "header_entity_path_hash_match": header_entity_path_hash_match,
            "header_entity_path_error": header_entity_path_error,
            "acceptance_datetime_et": acceptance,
            "acceptance_date_matches_filed_date": header.get("acceptance_date") == item["filing_date"],
            "acceptance_at_or_after_1730_et": acceptance_after_cutoff,
            "header_response_http_status": (header_headers or {}).get("http_status", ""),
        })
        sample_results.append(row_result)

    counts = Counter(row.get("index_status", "") for row in sample_results)
    header_checked = [row for row in sample_results if "header_identity_match" in row]
    header_matches = sum(bool(row["header_identity_match"]) for row in header_checked)
    identity_mismatches = [
        row["accession"] for row in header_checked if not row["header_identity_match"]
    ]
    found = [row for row in sample_results if row.get("index_accession_found")]
    owner_multiple = sum(row["reporting_owner_count"] > 1 for row in sample_results)
    acceptance_present = sum(bool(row.get("acceptance_datetime_et")) for row in header_checked)
    acceptance_after = sum(bool(row.get("acceptance_at_or_after_1730_et")) for row in header_checked)
    header_cik_in_index = sum(bool(row.get("header_identity_flags", {}).get("header_cik_in_index_entities")) for row in header_checked)
    issuer_cik_in_index = sum(bool(row.get("header_identity_flags", {}).get("issuer_cik_in_index_entities")) for row in header_checked)
    header_cik_owner_match = sum(bool(row.get("header_identity_flags", {}).get("header_cik_matches_reporting_owner")) for row in header_checked)
    header_cik_issuer_match = sum(bool(row.get("header_identity_flags", {}).get("header_cik_matches_issuer")) for row in header_checked)
    dual_path_checked = sum(
        row.get("header_entity_path_check_type") == "INDEPENDENT_ENTITY_PATH"
        and row.get("header_entity_path_hash_match") is not None
        for row in header_checked
    )
    dual_path_matches = sum(
        row.get("header_entity_path_check_type") == "INDEPENDENT_ENTITY_PATH"
        and row.get("header_entity_path_hash_match") is True
        for row in header_checked
    )
    same_path_identity_checks = sum(
        row.get("header_entity_path_check_type") == "SAME_ISSUER_PATH"
        and row.get("header_entity_path_hash_match") is True
        for row in header_checked
    )
    path_identity_checks_total = dual_path_checked + same_path_identity_checks
    header_path_check_types = dict(sorted(Counter(
        row.get("header_entity_path_check_type", "") for row in header_checked
    ).items()))
    header_cik_roles = dict(sorted(Counter(row.get("header_cik_role", "") for row in header_checked).items()))
    index_manifest_rows = list(index_manifests.values())
    all_index_counts = [row["counts"] for row in index_manifest_rows]
    index_parser_malformed = sum(row.get("malformed_rows", 0) for row in all_index_counts)
    index_conflicts = sum(row.get("conflicting_duplicate_accessions", 0) for row in all_index_counts)

    status = "PASS_BULK_TO_DAILY_INDEX_JOIN"
    if retrieval_errors or parser_errors or identity_mismatches or len(found) != 72:
        status = "PASS_WITH_QUARANTINED_EXCEPTIONS"
    result = {
        "phase": 320,
        "status": status,
        "date_utc": datetime.now(timezone.utc).date().isoformat(),
        "source_archives": source_archives,
        "sample": {
            "sampled_accessions": len(sample),
            "sampled_unique_accessions": len(sample_accessions),
            "prior_accessions_excluded": len(PRIOR_ACCESSIONS),
            "sample_is_probability_sample": False,
            "per_quarter": quarter_summary,
            "per_quarter_form_allocation": {q: SAMPLE_BINS for q in QUARTERS},
            "unique_bulk_filing_dates": len({row["filing_date"] for row in sample}),
            "multi_reporting_owner_accessions": owner_multiple,
        },
        "daily_index_join": {
            "unique_daily_index_files_downloaded": len(index_manifest_rows),
            "daily_index_bytes_downloaded": sum(row["bytes"] for row in index_manifest_rows),
            "bulk_accessions_found_on_filed_date": counts.get("MATCHED_ON_FILED_DATE", 0),
            "bulk_accessions_found_on_next_edgar_business_day": counts.get("MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY", 0),
            "bulk_accessions_not_found": counts.get("NOT_FOUND_ON_FILED_OR_NEXT_EDGAR_BUSINESS_DAY", 0),
            "index_identity_conflicts": counts.get("INDEX_IDENTITY_CONFLICT", 0),
            "accessions_with_issuer_entity_row": sum(bool(row.get("issuer_entity_row_present")) for row in found),
            "multi_entity_index_accessions": sum(row.get("index_entity_count", 0) > 1 for row in found),
            "index_parser_malformed_rows": index_parser_malformed,
            "index_parser_conflicting_accessions": index_conflicts,
        },
        "original_header_crosscheck": {
            "headers_downloaded": len(header_checked),
            "headers_identity_match": header_matches,
            "headers_identity_mismatch": len(identity_mismatches),
            "identity_mismatch_accessions": identity_mismatches,
            "acceptance_datetime_present": acceptance_present,
            "acceptance_at_or_after_1730_et": acceptance_after,
            "header_cik_in_index_entities": header_cik_in_index,
            "issuer_cik_in_index_entities": issuer_cik_in_index,
            "header_cik_matches_reporting_owner": header_cik_owner_match,
            "header_cik_matches_issuer": header_cik_issuer_match,
            "header_cik_roles": header_cik_roles,
            "dual_path_equivalence_checked": dual_path_checked,
            "dual_path_equivalence_verified": dual_path_matches,
            "dual_path_equivalence_mismatch": dual_path_checked - dual_path_matches,
            "same_path_identity_checks": same_path_identity_checks,
            "path_identity_checks_total": path_identity_checks_total,
            "header_path_check_types": header_path_check_types,
            "header_fetch_fallbacks": sum(row.get("header_fetch_source") == "index_entity_path_fallback" for row in header_checked),
        },
        "availability_interpretation": {
            "bulk_filing_date_matches_daily_index_date_for_all": counts.get("MATCHED_ON_FILED_DATE", 0) == 72,
            "daily_index_date_is_exact_first_public_receipt": False,
            "acceptance_datetime_is_exact_first_public_receipt": False,
            "transmission_start_time_observed": False,
            "strict_pit_admitted": False,
            "conservative_date_level_rule": (
                "Use the official SEC FILED AS OF DATE / daily-index date as a date-level anchor only; "
                "permit strategy use no earlier than the first full XNYS session strictly after that date. "
                "Do not substitute ACCEPTANCE-DATETIME for transmission commencement or first-public receipt."
            ),
        },
        "retrieval": {
            "http_request_errors": len(retrieval_errors),
            "parser_errors": len(parser_errors),
            "total_sec_bytes_downloaded": total_bytes[0],
            "raw_sec_bytes_uploaded": False,
            "retrieval_errors": retrieval_errors,
            "parser_error_details": parser_errors,
            "daily_index_manifest": index_manifest_rows,
        },
        "controls": {
            "strict_pit_admitted": False,
            "alpha_test_authorized": False,
            "return_test_run": False,
            "bootstrap_loo_run": False,
            "chronological_oos_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "raw_sec_bytes_uploaded": False,
            "vendor_contacted": False,
            "data_purchased": False,
            "email_sent": False,
        },
    }
    validate_result(result)
    _write_csv(output_dir / "phase320_bulk_daily_index_join_sample.csv", sample_results)
    _write_csv(output_dir / "phase320_daily_index_manifest.csv", index_manifest_rows)
    (output_dir / "phase320_bulk_daily_index_join_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("PHASE320_RESULT=" + json.dumps({
        "status": status,
        "sampled_accessions": len(sample),
        "daily_index_files": len(index_manifest_rows),
        "found_on_filed_date": counts.get("MATCHED_ON_FILED_DATE", 0),
        "found_next_business_day": counts.get("MATCHED_ON_NEXT_EDGAR_BUSINESS_DAY", 0),
        "not_found": counts.get("NOT_FOUND_ON_FILED_OR_NEXT_EDGAR_BUSINESS_DAY", 0),
        "headers_downloaded": len(header_checked),
        "headers_identity_match": header_matches,
        "request_errors": len(retrieval_errors),
        "parser_errors": len(parser_errors),
    }, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_audit(args.archive_dir, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))
    if result["status"] == "PASS_WITH_QUARANTINED_EXCEPTIONS":
        print("PHASE320_AUDIT_COMPLETED_WITH_QUARANTINED_EXCEPTIONS")


if __name__ == "__main__":
    main()
