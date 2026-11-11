"""Phase 294: retrieve stratified SEC Form 3/4/5 bulk archives.

Downloads six public quarterly ZIPs only when SEC_CONTACT_EMAIL is present.
Raw ZIPs are retained in the Actions artifact, never committed to the repository.
No alpha, PIT, production, universe, capital or holdout changes are authorized.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SAMPLE_ARCHIVES = {
    "2006Q1": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2006q1_form345.zip",
    "2012Q1": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2012q1_form345.zip",
    "2023Q1": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2023q1_form345.zip",
    "2023Q2": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2023q2_form345.zip",
    "2025Q3": "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/2025q3_form345.zip",
    "2026Q3": "https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q3_form345.zip",
}
TABLE_KEYS = {
    "SUBMISSION": ("ACCESSION_NUMBER",),
    "REPORTINGOWNER": ("ACCESSION_NUMBER", "RPTOWNERCIK"),
    "NONDERIV_TRANS": ("ACCESSION_NUMBER", "NONDERIV_TRANS_SK"),
    "NONDERIV_HOLDING": ("ACCESSION_NUMBER", "NONDERIV_HOLDING_SK"),
    "DERIV_TRANS": ("ACCESSION_NUMBER", "DERIV_TRANS_SK"),
    "DERIV_HOLDING": ("ACCESSION_NUMBER", "DERIV_HOLDING_SK"),
    "FOOTNOTES": ("ACCESSION_NUMBER", "FOOTNOTE_ID"),
    "OWNER_SIGNATURE": ("ACCESSION_NUMBER", "OWNERSIGNATURENAME"),
}
REQUIRED_TABLES = ("SUBMISSION", "REPORTINGOWNER", "NONDERIV_TRANS", "FOOTNOTES")
REQUIRED_FIELDS = {
    "SUBMISSION": {"ACCESSION_NUMBER", "DOCUMENT_TYPE", "FILING_DATE", "ISSUERCIK", "ISSUERTRADINGSYMBOL"},
    "REPORTINGOWNER": {"ACCESSION_NUMBER", "RPTOWNERCIK"},
    "NONDERIV_TRANS": {"ACCESSION_NUMBER", "NONDERIV_TRANS_SK", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES"},
    "FOOTNOTES": {"ACCESSION_NUMBER", "FOOTNOTE_ID"},
}
MAX_ARCHIVE_BYTES = 30 * 1024 * 1024
MAX_TOTAL_BYTES = 120 * 1024 * 1024
RETRIES = 4
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")


class RetrievalError(RuntimeError):
    pass


def _fetch(url: str, user_agent: str) -> tuple[bytes, dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "www.sec.gov":
        raise RetrievalError("non_sec_https_url_rejected")
    request = Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "application/zip, application/octet-stream, */*",
        "Accept-Encoding": "identity",
    })
    for attempt in range(RETRIES + 1):
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read(MAX_ARCHIVE_BYTES + 1)
                if len(payload) > MAX_ARCHIVE_BYTES:
                    raise RetrievalError("archive_size_limit_exceeded")
                headers = {
                    "http_status": str(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "date": response.headers.get("Date", ""),
                    "etag": response.headers.get("ETag", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                    "content_length": response.headers.get("Content-Length", ""),
                    "final_url_host": urlparse(response.geturl()).netloc,
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


def _table_member(zf: zipfile.ZipFile, table: str) -> zipfile.ZipInfo | None:
    matches = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        base = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
        stem = base.rsplit(".", 1)[0].upper()
        if stem == table:
            matches.append(info)
    if len(matches) > 1:
        raise ValueError(f"ambiguous_table_member:{table}")
    return matches[0] if matches else None


def _inspect_table(zf: zipfile.ZipFile, info: zipfile.ZipInfo, table: str,
                   submission_accessions: set[str] | None = None) -> dict[str, Any]:
    key_fields = TABLE_KEYS[table]
    summary: dict[str, Any] = {
        "member": info.filename,
        "uncompressed_bytes": info.file_size,
        "rows": 0,
        "header": [],
        "required_fields_present": True,
        "missing_key_rows": 0,
        "duplicate_primary_keys": 0,
        "orphan_accession_rows": 0,
        "accession_count": 0,
    }
    seen: set[tuple[str, ...]] = set()
    accessions: set[str] = set()
    with zf.open(info, "r") as raw:
        text_stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text_stream, delimiter="\t", quotechar='"')
        try:
            header = [x.strip().upper() for x in next(reader)]
        except StopIteration:
            raise ValueError(f"empty_table:{table}")
        if len(header) != len(set(header)):
            raise ValueError(f"duplicate_header_fields:{table}")
        summary["header"] = header
        summary["required_fields_present"] = REQUIRED_FIELDS.get(table, set()).issubset(set(header))
        if not summary["required_fields_present"]:
            summary["missing_required_fields"] = sorted(REQUIRED_FIELDS[table] - set(header))
        positions = {name: i for i, name in enumerate(header)}
        for row in reader:
            if not row:
                continue
            summary["rows"] += 1
            if len(row) != len(header):
                summary["malformed_rows"] = summary.get("malformed_rows", 0) + 1
                continue
            key = tuple(row[positions[k]].strip() if k in positions else "" for k in key_fields)
            if any(not x for x in key):
                summary["missing_key_rows"] += 1
            elif key in seen:
                summary["duplicate_primary_keys"] += 1
            else:
                seen.add(key)
            if "ACCESSION_NUMBER" in positions:
                accession = row[positions["ACCESSION_NUMBER"]].strip()
                if accession:
                    accessions.add(accession)
                    if submission_accessions is not None and accession not in submission_accessions:
                        summary["orphan_accession_rows"] += 1
        text_stream.detach()
    summary["accession_count"] = len(accessions)
    summary["unique_primary_keys"] = len(seen)
    return summary


def inspect_archive(payload: bytes, quarter: str) -> dict[str, Any]:
    archive_sha = hashlib.sha256(payload).hexdigest()
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        corrupt_member = zf.testzip()
        if corrupt_member:
            raise ValueError(f"zip_crc_failure:{corrupt_member}")
        tables: dict[str, zipfile.ZipInfo] = {}
        for table in TABLE_KEYS:
            member = _table_member(zf, table)
            if member is not None:
                tables[table] = member
        missing_required = sorted(set(REQUIRED_TABLES) - set(tables))
        if missing_required:
            raise ValueError(f"missing_required_tables:{','.join(missing_required)}")

        submission_summary = _inspect_table(zf, tables["SUBMISSION"], "SUBMISSION")
        submission_accessions: set[str] = set()
        form4_candidates: list[dict[str, str]] = []
        with zf.open(tables["SUBMISSION"], "r") as raw:
            stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(stream, delimiter="\t", quotechar='"')
            for row in reader:
                accession = (row.get("ACCESSION_NUMBER") or "").strip()
                if accession:
                    submission_accessions.add(accession)
                form = (row.get("DOCUMENT_TYPE") or "").strip().upper()
                if form in {"4", "4/A"} and ACCESSION_RE.fullmatch(accession):
                    form4_candidates.append({
                        "accession": accession,
                        "filing_date": (row.get("FILING_DATE") or "").strip(),
                        "document_type": form,
                        "issuer_cik": (row.get("ISSUERCIK") or "").strip(),
                        "issuer_ticker_as_filed": (row.get("ISSUERTRADINGSYMBOL") or "").strip(),
                    })
            stream.detach()

        table_summaries: dict[str, Any] = {"SUBMISSION": submission_summary}
        for table, info in tables.items():
            if table == "SUBMISSION":
                continue
            table_summaries[table] = _inspect_table(zf, info, table, submission_accessions)

        valid_form4 = [x for x in form4_candidates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", x["filing_date"])]
        valid_form4.sort(key=lambda x: (x["filing_date"], x["accession"]))
        if valid_form4:
            sample_indices = sorted(set((0, len(valid_form4) // 2, len(valid_form4) - 1)))
            form4_sample = [valid_form4[i] for i in sample_indices]
        else:
            form4_sample = []

        schema_issues = []
        for table in REQUIRED_TABLES:
            s = table_summaries[table]
            if not s["required_fields_present"]:
                schema_issues.append(f"{table}:required_fields_missing")
            if s.get("malformed_rows", 0):
                schema_issues.append(f"{table}:malformed_rows")
            if s["missing_key_rows"]:
                schema_issues.append(f"{table}:missing_key_rows")
            if s["duplicate_primary_keys"]:
                schema_issues.append(f"{table}:duplicate_primary_keys")
        orphan_total = sum(x["orphan_accession_rows"] for x in table_summaries.values())
        if orphan_total:
            schema_issues.append("orphan_accession_rows")
        if not valid_form4:
            schema_issues.append("no_valid_form4_rows")

        submission_header = table_summaries["SUBMISSION"]["header"]
        return {
            "quarter": quarter,
            "zip_sha256": archive_sha,
            "zip_bytes": len(payload),
            "zip_member_count": len(zf.infolist()),
            "zip_members": [x.filename for x in zf.infolist()],
            "tables_present": sorted(tables),
            "tables_missing_optional": sorted(set(TABLE_KEYS) - set(tables)),
            "table_summaries": table_summaries,
            "submission_aff10b5one_present": "AFF10B5ONE" in submission_header,
            "submission_rows": table_summaries["SUBMISSION"]["rows"],
            "form4_and_4a_rows": len(form4_candidates),
            "valid_form4_and_4a_rows": len(valid_form4),
            "form4_accession_sample": form4_sample,
            "orphan_accession_rows": orphan_total,
            "schema_gate_pass": not schema_issues,
            "schema_issues": schema_issues,
        }


def blocked_result() -> dict[str, Any]:
    return {
        "phase": 294,
        "status": "BLOCKED_MISSING_SEC_CONTACT_EMAIL",
        "email_secret_present": False,
        "archives_expected": len(SAMPLE_ARCHIVES),
        "archives_downloaded": 0,
        "raw_sec_requests": 0,
        "raw_archives_downloaded": 0,
        "strict_pit_admitted": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "decision": "No SEC request was made because SEC_CONTACT_EMAIL is absent or invalid.",
    }


def run_audit(email: str, output_dir: Path) -> dict[str, Any]:
    if not email or "@" not in email or any(ch.isspace() for ch in email):
        return blocked_result()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    user_agent = f"NuevaEstrategia Smart Money Research (contact: {email})"
    archives: list[dict[str, Any]] = []
    total_bytes = 0
    total_requests = 0
    for quarter, url in SAMPLE_ARCHIVES.items():
        item: dict[str, Any] = {"quarter": quarter, "url": url, "status": "PENDING"}
        try:
            payload, headers = _fetch(url, user_agent)
            total_requests += 1
            total_bytes += len(payload)
            if total_bytes > MAX_TOTAL_BYTES:
                raise RetrievalError("total_archive_size_limit_exceeded")
            parsed = inspect_archive(payload, quarter)
            path = raw_dir / f"{quarter.lower()}_form345.zip"
            path.write_bytes(payload)
            item.update({
                "status": "DOWNLOADED_AND_INSPECTED",
                "response_headers": headers,
                "archive": str(path.relative_to(output_dir)),
                **parsed,
            })
        except (RetrievalError, ValueError, zipfile.BadZipFile, csv.Error) as exc:
            item.update({"status": "RETRIEVAL_OR_SCHEMA_ERROR", "error_code": str(exc)[:240]})
        archives.append(item)
        time.sleep(0.5)
    downloaded = [x for x in archives if x["status"] == "DOWNLOADED_AND_INSPECTED"]
    schema_pass = [x for x in downloaded if x["schema_gate_pass"]]
    all_downloaded = len(downloaded) == len(SAMPLE_ARCHIVES)
    all_schema_pass = all_downloaded and len(schema_pass) == len(SAMPLE_ARCHIVES)
    status = (
        "SIX_ARCHIVES_RAW_RETRIEVED_SCHEMA_PASS"
        if all_schema_pass
        else "SIX_ARCHIVES_RAW_RETRIEVED_WITH_SCHEMA_ISSUES"
        if all_downloaded
        else "PARTIAL_RETRIEVAL_OR_SCHEMA"
        if downloaded
        else "RETRIEVAL_FAILED"
    )
    return {
        "phase": 294,
        "audit_as_of_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source": "SEC Insider Transactions Data Sets",
        "official_landing_page": "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets",
        "email_secret_present": True,
        "archives_expected": len(SAMPLE_ARCHIVES),
        "archives_downloaded": len(downloaded),
        "archives_schema_passed": len(schema_pass),
        "raw_sec_requests": total_requests,
        "raw_archives_downloaded": len(downloaded),
        "total_download_bytes": total_bytes,
        "archive_results": archives,
        "archive_sample_is_exhaustive": False,
        "archive_bytes_sha256_verified": all_downloaded,
        "strict_pit_admitted": False,
        "first_public_receipt_verified": False,
        "acceptance_time_reconciled": False,
        "multi_owner_transaction_attribution_verified": False,
        "effective_dated_security_class_identity_verified": False,
        "broad_universe_coverage_verified": False,
        "alpha_test_authorized": False,
        "return_test_run": False,
        "bootstrap_loo_run": False,
        "holdout_used": False,
        "f80_frozen": True,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "raw_archives_persisted_in_repository": False,
        "raw_archives_staged_for_actions_artifact": bool(downloaded),
        "data_purchase": False,
        "vendor_contact": False,
        "decision": "This is a stratified raw-byte/schema acquisition gate only. It does not establish first-public receipt, strict PIT, owner attribution, effective-dated security identity, broad-universe coverage or alpha. Raw ZIPs remain in the expiring Actions artifact and are not committed to the repository.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="phase294_output")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    result = run_audit(os.environ.get("SEC_CONTACT_EMAIL", "").strip(), output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase294_form4_bulk_sample_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
