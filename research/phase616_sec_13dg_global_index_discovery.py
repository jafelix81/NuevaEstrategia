#!/usr/bin/env python3
"""Bounded, global-index discovery and subject/filer validation for SEC 13D/G.

This phase deliberately does not use the legacy F80-filer-only accession panel.
The SEC master index CIK is treated as the filer; the archive path CIK is only
a candidate identity; the SEC-HEADER SUBJECT COMPANY block is authoritative
for subject-issuer identity. No ticker is inferred.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import posixpath
import random
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.phase485_sec_13dg_subject_filer_header_parser import (  # noqa: E402
    parse_subject_filer_identity,
)

SEC_ARCHIVES = "https://www.sec.gov/Archives/"
QUARTERS = ((2023, 4), (2024, 1), (2024, 3), (2024, 4), (2026, 3))
TARGET_FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
SAMPLE_SIZE = 44
REQUEST_DELAY_SECONDS = 0.65
MASTER_INDEX_FILE_RE = re.compile(r"^edgar/data/(\d{1,10})/((?:\d{10}-\d{2}-\d{6})|(?:\d{18}))\.txt$", re.I)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
ACCEPTANCE_RE = re.compile(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", re.I)


def normalize_cik(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text.isdigit() or len(text) > 10:
        return None
    return text.zfill(10)


def normalize_form(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def validate_user_agent(value: str | None) -> str:
    ua = str(value or "").strip()
    if not ua or not EMAIL_RE.search(ua):
        raise RuntimeError(
            "SEC_USER_AGENT is missing or does not contain a monitored contact email; "
            "no SEC request was made."
        )
    lowered = ua.lower()
    if any(token in lowered for token in ("example.com", "your-email", "replace-me", "placeholder")):
        raise RuntimeError(
            "SEC_USER_AGENT still contains a placeholder contact; no SEC request was made."
        )
    if len(ua) < 20:
        raise RuntimeError("SEC_USER_AGENT is not descriptive enough; no SEC request was made.")
    return ua


def filing_regimes(form: str, filing_date: date) -> tuple[str, str, str, bool]:
    form = normalize_form(form)
    family = "13D" if "13D" in form else "13G"
    amendment = form.endswith("/A")
    if family == "13D":
        legal = "PRE_2024_02_05" if filing_date < date(2024, 2, 5) else "POST_2024_02_05"
    else:
        legal = "PRE_2024_09_30" if filing_date < date(2024, 9, 30) else "POST_2024_09_30"
    if filing_date < date(2023, 12, 18):
        schema = "LEGACY_PRE_2023_12_18"
    elif filing_date < date(2024, 12, 18):
        schema = "VOLUNTARY_XML_2023_12_18_TO_2024_12_17"
    else:
        schema = "MANDATORY_XML_FROM_2024_12_18"
    return family, legal, schema, amendment


def accession_from_compact(value: str) -> str:
    compact = str(value or "").strip()
    if not re.fullmatch(r"\d{18}", compact):
        raise ValueError(f"Invalid 18-digit accession directory: {compact!r}")
    return f"{compact[:10]}-{compact[10:12]}-{compact[12:]}"


def build_index_header_url(filename: str, accession: str) -> tuple[str, str]:
    """Map the flat master.idx submission path to its accession-directory header URL.

    SEC master.idx filenames use edgar/data/{path_cik}/{accession}.txt. The
    accession-number subdirectory exists in the archive URL, but is not part
    of the master.idx Filename field; derive it from the validated accession.
    """
    path = str(filename or "").strip().lstrip("/")
    match = MASTER_INDEX_FILE_RE.fullmatch(path)
    if not match:
        raise ValueError(f"Master-index Filename is not an exact EDGAR submission path: {filename!r}")
    path_cik, accession_in_path = match.groups()
    compact = accession_in_path.replace("-", "")
    expected = accession.replace("-", "")
    if not re.fullmatch(r"\d{18}", expected) or compact != expected:
        raise ValueError("Master-index Filename accession does not match the parsed accession.")
    header_name = f"{accession}-index-headers.html"
    header_path = f"edgar/data/{path_cik}/{compact}/{header_name}"
    return urljoin(SEC_ARCHIVES, header_path), normalize_cik(path_cik) or ""


def parse_master_index(
    raw_text: str,
    *,
    index_url: str,
    index_sha256: str,
    quarter: str,
) -> list[dict[str, Any]]:
    lines = str(raw_text or "").splitlines()
    header_index = None
    for i, line in enumerate(lines):
        normalized = line.strip().lower().replace(" ", "")
        if normalized.startswith("cik|companyname|formtype|datefiled|filename"):
            header_index = i
            break
    if header_index is None:
        raise ValueError(f"SEC master index header not found in {index_url}")

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines[header_index + 1 :], start=header_index + 2):
        if not line.strip():
            continue
        if "|" not in line:
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            raise ValueError(f"Malformed master-index row at {index_url}:{line_number}")
        cik_raw, company_name, form_raw, filed_raw, filename = parts
        form = normalize_form(form_raw)
        if form not in TARGET_FORMS:
            continue
        index_company_cik = normalize_cik(cik_raw)
        try:
            filed = datetime.strptime(filed_raw.strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError(f"Invalid filing date at {index_url}:{line_number}") from exc
        path_match = MASTER_INDEX_FILE_RE.fullmatch(filename.strip().lstrip("/"))
        if not path_match:
            raise ValueError(f"Invalid SEC master-index Filename path at {index_url}:{line_number}")
        archive_path_cik = normalize_cik(path_match.group(1))
        accession = accession_from_compact(path_match.group(2).replace("-", ""))
        header_url, checked_path_cik = build_index_header_url(filename, accession)
        if checked_path_cik != archive_path_cik:
            raise ValueError("Archive path CIK normalization conflict.")
        accession_submitter_cik = accession[:10]
        family, legal, schema, amendment = filing_regimes(form, filed)
        rows.append(
            {
                "accession": accession,
                "accession_submitter_cik": accession_submitter_cik,
                "index_company_cik": index_company_cik,
                "index_company_name": company_name.strip(),
                "form": form,
                "form_family": family,
                "amendment": amendment,
                "filing_date": filed.isoformat(),
                "legal_regime": legal,
                "schema_regime": schema,
                "archive_path_cik": archive_path_cik,
                "filename": filename.strip().lstrip("/"),
                "primary_document": posixpath.basename(filename.strip()),
                "header_url": header_url,
                "index_url": index_url,
                "index_sha256": index_sha256,
                "index_row_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                "source_quarter": quarter,
                "index_company_accession_prefix_match": bool(index_company_cik and index_company_cik == accession_submitter_cik),
                "subject_issuer_cik": None,
                "subject_issuer_name": None,
                "filing_cik": None,
                "filing_entity_name": None,
                "header_acceptance_datetime": None,
                "header_sha256": None,
                "header_file": None,
                "identity_status": "NOT_RETRIEVED",
                "archive_path_subject_match": None,
                "archive_path_subject_status": "NOT_CHECKED",
                "header_subject_index_match": None,
                "header_filer_submitter_match": None,
                "research_observation_eligible": False,
                "public_availability_certified": False,
                "signal_eligible": False,
                "error": None,
            }
        )
    return rows


def deduplicate_index_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_accession: dict[str, dict[str, Any]] = {}
    for row in rows:
        accession = row["accession"]
        if accession not in by_accession:
            row["duplicate_index_occurrences"] = 0
            by_accession[accession] = row
            continue
        prior = by_accession[accession]
        keys = ("index_company_cik", "form", "filing_date", "filename")
        if any(prior.get(key) != row.get(key) for key in keys):
            raise ValueError(f"Conflicting global-index rows for accession {accession}")
        prior["duplicate_index_occurrences"] += 1
    return list(by_accession.values())


def stratified_sample(
    rows: list[dict[str, Any]],
    sample_size: int = SAMPLE_SIZE,
    *,
    required_quarters: set[str] | None = None,
) -> list[dict[str, Any]]:
    eligible = [r for r in rows if r.get("index_company_cik")]
    expected_quarters = (
        set(required_quarters)
        if required_quarters is not None
        else {f"{year}Q{quarter}" for year, quarter in QUARTERS}
    )
    observed_quarters = {str(r.get("source_quarter") or "") for r in eligible}
    missing_source_quarters = expected_quarters - observed_quarters
    if missing_source_quarters:
        raise ValueError(
            "Global index input is missing preregistered quarters: "
            + ", ".join(sorted(missing_source_quarters))
        )

    buckets: dict[tuple[str, str, bool, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        key = (
            str(row.get("source_quarter") or ""),
            row["form_family"],
            bool(row["amendment"]),
            row["legal_regime"],
            row["schema_regime"],
        )
        buckets[key].append(row)
    for values in buckets.values():
        values.sort(key=lambda r: hashlib.sha256(r["accession"].encode()).hexdigest())

    keys = sorted(buckets)
    selected: list[dict[str, Any]] = []
    cursor = {key: 0 for key in keys}
    while len(selected) < sample_size:
        progressed = False
        for key in keys:
            index = cursor[key]
            if index < len(buckets[key]):
                selected.append(buckets[key][index])
                cursor[key] += 1
                progressed = True
                if len(selected) == sample_size:
                    break
        if not progressed:
            break
    if len(selected) != sample_size:
        raise ValueError(
            f"Global index sample has only {len(selected)} eligible accessions; "
            f"{sample_size} required."
        )
    present_forms = {str(row.get("form") or "") for row in selected}
    missing_forms = TARGET_FORMS - present_forms
    if missing_forms:
        raise ValueError(
            "Stratified sample does not cover all four Schedule 13D/G forms: "
            + ", ".join(sorted(missing_forms))
        )
    selected_quarters = {str(row.get("source_quarter") or "") for row in selected}
    missing_sample_quarters = expected_quarters - selected_quarters
    if missing_sample_quarters:
        raise ValueError(
            "Stratified sample does not represent every preregistered quarter: "
            + ", ".join(sorted(missing_sample_quarters))
        )
    return selected

def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fetch_bytes(url: str, user_agent: str, *, delay_seconds: float = REQUEST_DELAY_SECONDS) -> bytes:
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip",
    }
    last_error: Exception | None = None
    for attempt in range(7):
        try:
            with urlopen(Request(url, headers=headers), timeout=60) as response:
                raw = response.read()
                encoding = (response.headers.get("Content-Encoding") or "").lower()
                if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return raw
        except HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                raise
            if exc.code not in (403, 429, 500, 502, 503, 504):
                raise
            if exc.code == 403:
                raise RuntimeError(
                    "SEC returned HTTP 403. Verify SEC_USER_AGENT and the repository's "
                    "SEC access configuration; the contact value was not logged."
                ) from exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                wait = float(retry_after) if retry_after else min(60.0, 2.0**attempt)
            except (TypeError, ValueError):
                wait = min(60.0, 2.0**attempt)
            time.sleep(wait + random.random() * 0.25)
        except Exception as exc:
            last_error = exc
            time.sleep(min(30.0, 2.0**attempt) + random.random() * 0.25)
    raise RuntimeError(f"SEC request failed after retries: {url}: {last_error}")


def acceptance_datetime(header_text: str) -> str | None:
    match = ACCEPTANCE_RE.search(str(header_text or ""))
    if not match:
        return None
    return match.group(1)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_live_sample(output_dir: Path, *, sample_size: int = SAMPLE_SIZE) -> dict[str, Any]:
    user_agent = validate_user_agent(os.environ.get("SEC_USER_AGENT"))
    output_dir.mkdir(parents=True, exist_ok=True)
    index_dir = output_dir / "indexes"
    header_dir = output_dir / "headers"
    index_dir.mkdir(exist_ok=True)
    header_dir.mkdir(exist_ok=True)

    index_manifest: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for year, quarter in QUARTERS:
        qlabel = f"{year}Q{quarter}"
        index_url = (
            f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
        )
        raw = fetch_bytes(index_url, user_agent)
        index_path = index_dir / f"master_{year}_QTR{quarter}.idx"
        index_path.write_bytes(raw)
        index_hash = sha256_bytes(raw)
        parsed = parse_master_index(
            raw.decode("utf-8-sig", "replace"),
            index_url=index_url,
            index_sha256=index_hash,
            quarter=qlabel,
        )
        all_rows.extend(parsed)
        index_manifest.append(
            {
                "quarter": qlabel,
                "url": index_url,
                "sha256": index_hash,
                "bytes": len(raw),
                "target_form_rows": len(parsed),
            }
        )

    unique_rows = deduplicate_index_rows(all_rows)
    sample = stratified_sample(unique_rows, sample_size=sample_size)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for row in sample:
        result = dict(row)
        try:
            raw_header = fetch_bytes(row["header_url"], user_agent)
            header_text = raw_header.decode("utf-8", "replace")
            header_hash = sha256_bytes(raw_header)
            header_path = header_dir / f"{row['accession']}.txt"
            header_path.write_bytes(raw_header)
            identity = parse_subject_filer_identity(header_text, row["accession"])
            result.update(
                {
                    "subject_issuer_cik": identity.get("subject_issuer_cik"),
                    "subject_issuer_name": identity.get("subject_issuer_name"),
                    "filing_cik": identity.get("filing_cik"),
                    "filing_entity_name": identity.get("filing_entity_name"),
                    "header_acceptance_datetime": acceptance_datetime(header_text),
                    "header_sha256": header_hash,
                    "header_file": str(header_path.relative_to(output_dir)),
                    "identity_status": identity.get("identity_status"),
                    "archive_path_subject_match": (
                        identity.get("subject_issuer_cik") == row.get("archive_path_cik")
                    ),
                    "header_subject_index_match": (
                        identity.get("subject_issuer_cik") == row.get("index_company_cik")
                    ),
                    "header_filer_submitter_match": (
                        identity.get("filing_cik") == row.get("accession_submitter_cik")
                    ),
                }
            )
            if not identity.get("subject_issuer_identity_verified"):
                result["identity_status"] = str(identity.get("identity_status"))
            elif not result["header_subject_index_match"]:
                result["identity_status"] = "HEADER_SUBJECT_INDEX_COMPANY_MISMATCH"
            else:
                result["identity_status"] = "VERIFIED_SUBJECT_AND_FILER"
            result["archive_path_subject_status"] = (
                "MATCH" if result["archive_path_subject_match"] else "MISMATCH_REQUIRES_REVIEW"
            )
        except Exception as exc:
            result["identity_status"] = "HEADER_RETRIEVAL_OR_PARSE_ERROR"
            result["error"] = f"{type(exc).__name__}: {exc}"
            errors.append({"accession": row["accession"], "error": result["error"]})
        results.append(result)

    verified = sum(r["identity_status"] == "VERIFIED_SUBJECT_AND_FILER" for r in results)
    sample_quarters = sorted({str(r.get("source_quarter") or "") for r in sample})
    sample_quarter_coverage_complete = set(sample_quarters) == {
        f"{year}Q{quarter}" for year, quarter in QUARTERS
    }
    sample_form_coverage_complete = {r["form"] for r in sample} == TARGET_FORMS
    sample_gate_complete = (
        verified == sample_size
        and sample_quarter_coverage_complete
        and sample_form_coverage_complete
    )
    summary = {
        "phase": 616,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETE" if sample_gate_complete else "QUARANTINED",
        "quarterly_indexes": index_manifest,
        "target_forms": sorted(TARGET_FORMS),
        "global_index_target_rows": len(all_rows),
        "unique_accessions": len(unique_rows),
        "duplicate_index_occurrences": sum(r.get("duplicate_index_occurrences", 0) for r in unique_rows),
        "sample_size_requested": sample_size,
        "sample_size_retrieved": len(results),
        "sample_identity_verified": verified,
        "identity_status_counts": {},
        "form_counts": {},
        "legal_regime_counts": {},
        "schema_regime_counts": {},
        "global_index_company_accession_prefix_mismatches": sum(
            not r.get("index_company_accession_prefix_match") for r in unique_rows
        ),
        "sample_index_company_accession_prefix_mismatches": sum(
            not r.get("index_company_accession_prefix_match") for r in results
        ),
        "sample_form_coverage_complete": sample_form_coverage_complete,
        "sample_quarters": sample_quarters,
        "sample_quarter_coverage_complete": sample_quarter_coverage_complete,
        "header_subject_index_mismatches": sum(r.get("header_subject_index_match") is False for r in results),
        "header_filer_submitter_mismatches": sum(r.get("header_filer_submitter_match") is False for r in results),
        "archive_path_subject_mismatches": sum(r.get("archive_path_subject_match") is False for r in results),
        "header_errors": len(errors),
        "errors_sample": errors[:20],
        "subject_ticker_mapping": "NOT_ATTEMPTED",
        "effective_dated_f80_membership": "NOT_ATTEMPTED",
        "public_availability_certified": False,
        "research_observation_eligible": False,
        "signal_eligible": False,
        "alpha_test_authorized": False,
        "gate": "PASS_HEADER_IDENTITY_ONLY" if sample_gate_complete else "FAIL",
        "limitations": [
            "The SEC master-index CIK/company-name pair is a subject-company candidate and must match the SEC-HEADER SUBJECT COMPANY CIK.",
            "FILED BY is a separate filing-entity identity. The accession prefix is an EDGAR login/submitter CIK and may belong to a third-party filing agent; it is not required to equal FILED BY or the master-index CIK.",
            "Archive-path CIK is a retrieval locator and diagnostic only; it is never used as the subject identity.",
            "ACCEPTANCE-DATETIME is preserved for chronology only; it is not exact public availability.",
            "No primary schedule, holdings, ticker mapping, historical F80 membership, prices or returns are downloaded or inferred.",
            "The 44-accession sample is a parser/discovery feasibility gate, not a coverage estimate or alpha test.",
        ],
    }
    for key, counter_key in (
        ("identity_status", "identity_status_counts"),
        ("form", "form_counts"),
        ("legal_regime", "legal_regime_counts"),
        ("schema_regime", "schema_regime_counts"),
    ):
        counts: dict[str, int] = {}
        for row in results:
            value = str(row.get(key) or "UNKNOWN")
            counts[value] = counts.get(value, 0) + 1
        summary[counter_key] = counts

    write_csv(output_dir / "global_13dg_index_sample.csv", results)
    (output_dir / "index_manifest.json").write_text(
        json.dumps(index_manifest, indent=2), encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    if not sample_gate_complete:
        raise RuntimeError(
            f"Bounded SEC 13D/G identity gate failed: {verified}/{sample_size} verified. "
            "Artifacts were written for review; no full crawl is authorized."
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-sample", action="store_true")
    parser.add_argument("--output-dir", default="phase616_sec_13dg_global_index_sample")
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE)
    args = parser.parse_args()
    if not args.live_sample:
        raise SystemExit("Use --live-sample only from the explicit manual workflow.")
    if args.sample_size != SAMPLE_SIZE:
        raise SystemExit(f"Only the preregistered sample size {SAMPLE_SIZE} is permitted.")
    summary = run_live_sample(Path(args.output_dir), sample_size=args.sample_size)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
