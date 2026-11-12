#!/usr/bin/env python3
"""Retrieve and validate the 44 exact SEC 13D/G predecessor references from Phase 349."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SEC_BASE = "https://www.sec.gov/Archives/edgar/data/"
PROJECT_URL = "https://github.com/jafelix81/NuevaEstrategia"


def digits_only(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def normalize_accession(value):
    digits = digits_only(value)
    if len(digits) != 18:
        return ""
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def normalize_cik(value):
    digits = digits_only(value)
    return digits.zfill(10) if digits and len(digits) <= 10 else digits


def family_from_form(form):
    value = str(form or "").upper()
    if re.search(r"\b13D\b", value):
        return "13D"
    if re.search(r"\b13G\b", value):
        return "13G"
    return ""


def build_archive_url(parent_accession, archive_path_cik):
    accession = normalize_accession(parent_accession)
    path_cik = normalize_cik(archive_path_cik)
    if not accession or not path_cik:
        raise ValueError("Invalid parent accession or archive-path CIK")
    accession_prefix = accession.split("-")[0]
    if path_cik != accession_prefix:
        raise ValueError("Archive-path CIK must equal the first ten accession digits; it is not issuer identity")
    path_cik_unpadded = str(int(path_cik))
    accession_no_dashes = digits_only(accession)
    return f"{SEC_BASE}{path_cik_unpadded}/{accession_no_dashes}/{accession}.txt"


def parse_acceptance_utc(header):
    match = re.search(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", header, re.IGNORECASE)
    if not match:
        match = re.search(r"ACCEPTANCE-DATETIME\s*:\s*(\d{14})", header, re.IGNORECASE)
    if not match:
        return ""
    local = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(
        tzinfo=ZoneInfo("America/New_York")
    )
    return local.astimezone(timezone.utc).isoformat()


def parse_sec_header(raw_text):
    match = re.search(r"<SEC-HEADER>(.*?)</SEC-HEADER>", raw_text, re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError("SEC-HEADER block not found")
    header = match.group(1)

    def field(pattern):
        found = re.search(pattern, header, re.IGNORECASE | re.MULTILINE)
        return found.group(1).strip() if found else ""

    accession = normalize_accession(field(r"ACCESSION NUMBER\s*:\s*([0-9-]{20})"))
    form = field(r"CONFORMED SUBMISSION TYPE\s*:\s*([^\r\n]+)")
    filed_raw = field(r"FILED AS OF DATE\s*:\s*(\d{8})")
    filed_date = f"{filed_raw[:4]}-{filed_raw[4:6]}-{filed_raw[6:8]}" if len(filed_raw) == 8 else ""

    subject_cik = ""
    subject_start = re.search(r"SUBJECT COMPANY\s*:", header, re.IGNORECASE)
    if subject_start:
        tail = header[subject_start.end():]
        boundaries = [
            m.start() for m in re.finditer(r"^\s*(?:FILED BY|REPORTING-OWNER)\s*:", tail, re.IGNORECASE | re.MULTILINE)
        ]
        subject_block = tail[:min(boundaries)] if boundaries else tail
        cik_match = re.search(r"CENTRAL INDEX KEY\s*:\s*(\d{1,10})", subject_block, re.IGNORECASE)
        if cik_match:
            subject_cik = normalize_cik(cik_match.group(1))

    acceptance_utc = parse_acceptance_utc(header)
    return {
        "header_accession": accession,
        "parent_form": form,
        "parent_form_family": family_from_form(form),
        "parent_filing_date": filed_date,
        "parent_subject_cik": subject_cik,
        "parent_acceptance_utc": acceptance_utc,
        "header_parse_status": "PARSED",
    }


def validate_parent_metadata(parent, expected):
    reasons = []
    if parent.get("header_accession") != expected.get("explicit_parent_accession"):
        reasons.append("parent_accession_mismatch")
    if not parent.get("parent_subject_cik"):
        reasons.append("parent_subject_cik_missing")
    elif parent.get("parent_subject_cik") != normalize_cik(expected.get("subject_issuer_cik")):
        reasons.append("parent_subject_cik_mismatch")
    if not parent.get("parent_form_family"):
        reasons.append("parent_form_family_unrecognized")
    elif parent.get("parent_form_family") != str(expected.get("form_family", "")).upper():
        reasons.append("parent_form_family_mismatch")
    if not parent.get("parent_acceptance_utc"):
        reasons.append("parent_acceptance_missing")
    elif not expected.get("child_acceptance_utc"):
        reasons.append("child_acceptance_missing")
    else:
        parent_time = datetime.fromisoformat(parent["parent_acceptance_utc"])
        child_time = datetime.fromisoformat(expected["child_acceptance_utc"])
        if parent_time >= child_time:
            reasons.append("parent_acceptance_not_strictly_earlier")
    return reasons


def request_submission(url, user_agent, pause_seconds=0.5, max_retries=3):
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/plain, */*",
        "Accept-Encoding": "identity",
        "Host": "www.sec.gov",
        "Connection": "close",
    }
    last_error = ""
    for attempt in range(max_retries):
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=45) as response:
                body = response.read()
                status = getattr(response, "status", 200)
                time.sleep(pause_seconds)
                return status, body, "", False, False
        except HTTPError as error:
            status = error.code
            detail = error.read(2048).decode("utf-8", errors="replace")
            time.sleep(pause_seconds)
            if status == 404:
                return status, b"", "HTTP 404: parent accession not found", False, False
            if status == 403:
                return status, b"", "HTTP 403: SEC denied the declared automated request", True, False
            if status == 429:
                retry_after = error.headers.get("Retry-After", "")
                try:
                    delay = max(float(retry_after), 2.0)
                except (TypeError, ValueError):
                    delay = 2.0 * (attempt + 1)
                last_error = f"HTTP 429 rate limit; retry-after={retry_after}; body={detail[:200]}"
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                return status, b"", last_error, False, True
            if status >= 500 and attempt < max_retries - 1:
                last_error = f"HTTP {status}; retrying"
                time.sleep(2.0 * (attempt + 1))
                continue
            return status, b"", f"HTTP {status}: {detail[:300]}", False, status >= 500
        except URLError as error:
            last_error = f"URL error: {error}"
            if attempt < max_retries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            return 0, b"", last_error, False, True
        except TimeoutError as error:
            last_error = f"Timeout: {error}"
            if attempt < max_retries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            return 0, b"", last_error, False, True
    return 0, b"", last_error or "Unknown retrieval failure", False, True


def load_manifest(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 44:
        raise ValueError(f"Expected 44 Phase 349 targets, found {len(rows)}")
    parents = [normalize_accession(row.get("explicit_parent_accession")) for row in rows]
    if any(not x for x in parents) or len(set(parents)) != 44:
        raise ValueError("Parent accessions must be 44 unique valid SEC accessions")
    return rows


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args):
    user_agent = args.user_agent or ""
    if not user_agent.strip():
        raise ValueError("A declared SEC_USER_AGENT is required")
    manifest = load_manifest(args.manifest)
    out = Path(args.outdir)
    raw_dir = out / "parents"
    raw_dir.mkdir(parents=True, exist_ok=True)

    results = []
    http_counts = Counter()
    stop_reason = ""
    for index, expected in enumerate(manifest, start=1):
        parent_accession = normalize_accession(expected["explicit_parent_accession"])
        try:
            url = build_archive_url(parent_accession, expected["parent_archive_path_cik"])
        except ValueError as error:
            results.append({
                "child_accession": expected["child_accession"],
                "parent_accession": parent_accession,
                "retrieval_status": "MANIFEST_PATH_ERROR",
                "http_status": 0,
                "raw_sha256": "",
                "validation_reasons": str(error),
                "reference_validation_status": "QUARANTINE",
                "immediate_predecessor_claimed": False,
            })
            continue

        print(f"[{index}/44] GET {parent_accession} via archive-path CIK {expected['parent_archive_path_cik']}")
        status, body, error_text, blocked, retryable = request_submission(
            url, user_agent, pause_seconds=1.0 / max(args.requests_per_second, 0.5)
        )
        http_counts[str(status)] += 1
        record = {
            "child_accession": expected["child_accession"],
            "parent_accession": parent_accession,
            "subject_issuer_cik": expected["subject_issuer_cik"],
            "child_filer_cik": expected["child_filer_cik"],
            "parent_archive_path_cik": expected["parent_archive_path_cik"],
            "parent_path_cik_role": "ARCHIVE_PATH_ONLY_NOT_ISSUER_IDENTITY",
            "form_family_expected": expected["form_family"],
            "child_acceptance_utc": expected["child_acceptance_utc"],
            "url": url,
            "http_status": status,
            "raw_bytes": len(body),
            "raw_sha256": "",
            "retrieval_status": "HTTP_ERROR",
            "header_accession": "",
            "parent_form": "",
            "parent_form_family": "",
            "parent_filing_date": "",
            "parent_subject_cik": "",
            "parent_acceptance_utc": "",
            "accession_match": False,
            "subject_cik_match": False,
            "form_family_match": False,
            "acceptance_strictly_earlier": False,
            "reference_validation_status": "QUARANTINE",
            "validation_reasons": error_text,
            "immediate_predecessor_claimed": False,
        }
        if status == 200 and body:
            raw_path = raw_dir / f"{parent_accession.replace('-', '')}.txt"
            raw_path.write_bytes(body)
            record["raw_sha256"] = hashlib.sha256(body).hexdigest()
            record["retrieval_status"] = "HTTP_200"
            try:
                raw_text = body.decode("utf-8", errors="replace")
                parsed = parse_sec_header(raw_text)
                reasons = validate_parent_metadata(parsed, expected)
                record.update(parsed)
                record["accession_match"] = parsed["header_accession"] == parent_accession
                record["subject_cik_match"] = parsed["parent_subject_cik"] == normalize_cik(expected["subject_issuer_cik"])
                record["form_family_match"] = parsed["parent_form_family"] == expected["form_family"]
                if parsed["parent_acceptance_utc"] and expected.get("child_acceptance_utc"):
                    record["acceptance_strictly_earlier"] = (
                        datetime.fromisoformat(parsed["parent_acceptance_utc"])
                        < datetime.fromisoformat(expected["child_acceptance_utc"])
                    )
                record["validation_reasons"] = ";".join(reasons)
                record["reference_validation_status"] = "VALID_EXPLICIT_REFERENCE" if not reasons else "QUARANTINE"
            except Exception as error:
                record["retrieval_status"] = "HEADER_PARSE_FAILED"
                record["validation_reasons"] = f"header_parse_error:{type(error).__name__}:{error}"
        elif status == 404:
            record["retrieval_status"] = "NOT_FOUND"
        elif blocked:
            record["retrieval_status"] = "BLOCKED_SEC_ACCESS"
            record["validation_reasons"] = error_text
            stop_reason = "SEC returned HTTP 403; stop further requests and require a declared contact route"
        elif retryable:
            record["retrieval_status"] = "RETRYABLE_TRANSPORT_OR_RATE_LIMIT"
            record["validation_reasons"] = error_text
            stop_reason = "Transient transport/rate-limit failure; stop to avoid repeated requests"
        results.append(record)
        if blocked or retryable:
            break

    out.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in results for key in row})
    with (out / "phase350_parent_retrieval.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    valid = sum(row.get("reference_validation_status") == "VALID_EXPLICIT_REFERENCE" for row in results)
    quarantined = sum(row.get("reference_validation_status") == "QUARANTINE" for row in results)
    saved = sum(bool(row.get("raw_sha256")) for row in results)
    blocked = any(row.get("retrieval_status") == "BLOCKED_SEC_ACCESS" for row in results)
    retryable = any(row.get("retrieval_status") == "RETRYABLE_TRANSPORT_OR_RATE_LIMIT" for row in results)
    if blocked:
        status = "BLOCKED_SEC_ACCESS"
    elif retryable:
        status = "PARTIAL_RETRYABLE_FAILURE"
    elif len(results) < len(manifest):
        status = "PARTIAL"
    elif valid == len(manifest):
        status = "COMPLETE_VALID_EXPLICIT_REFERENCES"
    elif saved == len(manifest):
        status = "COMPLETE_WITH_QUARANTINE"
    else:
        status = "PARTIAL_OR_QUARANTINED"

    summary = {
        "phase": "350-sec-13dg-explicit-parent-retrieval",
        "status": status,
        "target_references": len(manifest),
        "requests_attempted": len(results),
        "http_status_counts": dict(sorted(http_counts.items())),
        "raw_parent_documents_saved": saved,
        "header_parse_success_rows": sum(row.get("header_parse_status") == "PARSED" for row in results),
        "valid_explicit_reference_rows": valid,
        "quarantined_or_unvalidated_rows": quarantined,
        "not_found_rows": sum(row.get("retrieval_status") == "NOT_FOUND" for row in results),
        "sec_access_blocked": blocked,
        "retryable_stop": retryable,
        "stop_reason": stop_reason,
        "request_rate_per_second": args.requests_per_second,
        "new_sec_requests_made": True,
        "archive_path_cik_used_only_for_url": True,
        "immediate_predecessor_inference_performed": False,
        "sec_first_publication_timestamp_available": False,
        "conservative_event_execution_rule": "NEXT_TRADING_SESSION_AFTER_ACCEPTANCE",
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "f80_frozen": True,
    }
    write_json(out / "phase350_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 2 if blocked else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("phase350_output"))
    parser.add_argument("--user-agent", default="")
    parser.add_argument("--requests-per-second", type=float, default=2.0)
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
