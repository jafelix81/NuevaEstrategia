#!/usr/bin/env python3
"""Phase 311: SEC EDGAR quarterly master-index census for N-PORT filings.

This is an accession-inventory feasibility audit only. It does not download
portfolio holdings, infer first-public timestamps, map securities to F80, or
test returns. Exact NPORT-P and NPORT-P/A form tokens are retained separately.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import requests

TARGET_FORMS = {"NPORT-P", "NPORT-P/A"}
HEADER = "CIK|Company Name|Form Type|Date Filed|Filename"
BASE_URL = "https://www.sec.gov/Archives/edgar/full-index"
DATASET_URL = "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets"
README_URL = "https://www.sec.gov/files/nport_readme.pdf"


def quarter_bounds(quarter: str) -> tuple[date, date]:
    match = re.fullmatch(r"(20\d{2})Q([1-4])", str(quarter).upper())
    if not match:
        raise ValueError("invalid_quarter")
    year, q = int(match.group(1)), int(match.group(2))
    start_month = (q - 1) * 3 + 1
    start = date(year, start_month, 1)
    if q == 4:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, start_month + 3, 1)
    return start, end


def quarter_list(start: str = "2019Q4", end: str = "2026Q3") -> list[str]:
    sy, sq = int(start[:4]), int(start[-1])
    ey, eq = int(end[:4]), int(end[-1])
    if (sy, sq) > (ey, eq):
        raise ValueError("start_after_end")
    out = []
    year, q = sy, sq
    while (year, q) <= (ey, eq):
        out.append(f"{year}Q{q}")
        q += 1
        if q == 5:
            year += 1
            q = 1
    return out


def accession_from_filename(filename: str, row_cik: str) -> str:
    path_match = re.search(r"(?:^|/)edgar/data/(\d+)/(.*)$", filename.strip(), flags=re.I)
    if not path_match:
        raise ValueError(f"target_form_filename_missing_accession_path:{filename!r}")
    path_cik = path_match.group(1).zfill(10)
    if path_cik != str(row_cik).strip().zfill(10):
        raise ValueError("index_cik_path_cik_mismatch")

    tail = path_match.group(2).strip()
    # Current index paths commonly use an 18-digit accession directory;
    # older master indexes can instead point directly to an accession-named
    # complete-submission text file with the canonical 10-2-6 hyphenation.
    folder = re.match(r"(\d{18})(?:/|$)", tail)
    dashed_file = re.match(r"(\d{10}-\d{2}-\d{6})(?:\.txt)?$", tail, flags=re.I)
    compact_file = re.match(r"(\d{18})\.txt$", tail, flags=re.I)
    if folder:
        accession_digits = folder.group(1)
    elif dashed_file:
        accession_digits = dashed_file.group(1).replace("-", "")
    elif compact_file:
        accession_digits = compact_file.group(1)
    else:
        raise ValueError(f"target_form_filename_accession_unrecognized:{filename!r}")
    return f"{accession_digits[:10]}-{accession_digits[10:12]}-{accession_digits[12:]}"


def parse_master_index(text: str, quarter: str) -> list[dict[str, str]]:
    start, end = quarter_bounds(quarter)
    lines = text.splitlines()
    try:
        header_index = next(i for i, line in enumerate(lines) if line.strip() == HEADER)
    except StopIteration as exc:
        raise ValueError("master_index_header_missing") from exc

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    malformed_target_rows = 0
    for line in lines[header_index + 1:]:
        raw = line.strip("\r\n")
        if not raw or raw.startswith("-"):
            continue
        try:
            cik, remainder = raw.split("|", 1)
            company_name, form_type, filed, filename = remainder.rsplit("|", 3)
        except ValueError:
            if "NPORT-P" in raw:
                malformed_target_rows += 1
            continue
        cik, company_name, form_type, filed, filename = [
            x.strip() for x in (cik, company_name, form_type, filed, filename)
        ]
        if form_type not in TARGET_FORMS:
            continue
        if not cik.isdigit() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", filed):
            raise ValueError("target_row_invalid_cik_or_filing_date")
        filed_date = date.fromisoformat(filed)
        if not (start <= filed_date < end):
            raise ValueError("target_row_outside_quarter")
        accession = accession_from_filename(filename, cik)
        if accession in seen:
            raise ValueError("duplicate_accession_within_quarter")
        seen.add(accession)
        rows.append({
            "quarter": quarter,
            "accession": accession,
            "cik": cik.zfill(10),
            "company_name": company_name,
            "form_type": form_type,
            "filing_date": filed,
            "filename": filename,
        })
    if malformed_target_rows:
        raise ValueError("malformed_target_rows")
    return rows


def parse_master_zip(payload: bytes, quarter: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [n for n in archive.namelist() if n.lower().endswith("master.idx")]
        if len(members) != 1:
            raise ValueError("master_zip_must_contain_exactly_one_master_idx")
        raw = archive.read(members[0])
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return parse_master_index(text, quarter)


def select_stratified_sample(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Select at most one deterministic accession per quarter and exact form.

    The hash ordering avoids selecting only the newest/oldest filing. This is a
    reproducible QA sample, not a random or representative prevalence sample.
    """
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["quarter"], row["form_type"])].append(row)
    selected = []
    for (quarter, form_type), items in sorted(groups.items()):
        chosen = min(
            items,
            key=lambda x: hashlib.sha256(
                ("phase311-nport-sample-v1|" + x["accession"]).encode("ascii")
            ).hexdigest(),
        )
        selected.append({
            **chosen,
            "sample_rule": "min_sha256_phase311_nport_sample_v1_per_quarter_form",
            "sample_group_size": str(len(items)),
        })
    return selected


def _download_quarter(session: requests.Session, quarter: str, output_dir: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    year, q = quarter[:4], quarter[-1]
    url = f"{BASE_URL}/{year}/QTR{q}/master.zip"
    last_error = None
    payload = None
    for attempt in range(5):
        try:
            response = session.get(url, timeout=(20, 120))
            response.raise_for_status()
            payload = response.content
            break
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if attempt < 4:
                time.sleep(1.5 * (attempt + 1))
    if payload is None:
        raise RuntimeError(f"download_failed:{quarter}:{last_error}")
    if len(payload) < 1000:
        raise RuntimeError(f"archive_too_small:{quarter}:{len(payload)}")
    digest = hashlib.sha256(payload).hexdigest()
    rows = parse_master_zip(payload, quarter)
    metadata = {
        "quarter": quarter,
        "url": url,
        "http_status": response.status_code,
        "archive_bytes": len(payload),
        "archive_sha256": digest,
        "target_accessions": len(rows),
        "nport_p": sum(1 for x in rows if x["form_type"] == "NPORT-P"),
        "nport_p_a": sum(1 for x in rows if x["form_type"] == "NPORT-P/A"),
        "distinct_registrant_ciks": len({x["cik"] for x in rows}),
        "filing_date_min": min((x["filing_date"] for x in rows), default=None),
        "filing_date_max": max((x["filing_date"] for x in rows), default=None),
    }
    return rows, metadata


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_census(start: str, end: str, output_dir: Path, contact_email: str) -> dict[str, Any]:
    if not contact_email or "@" not in contact_email:
        raise RuntimeError("SEC_CONTACT_EMAIL_secret_missing_or_invalid")
    quarters = quarter_list(start, end)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": f"NuevaEstrategia quantitative research contact {contact_email}",
        "Accept": "application/zip,application/octet-stream,*/*",
        "Accept-Encoding": "gzip, deflate",
    })

    all_rows: list[dict[str, str]] = []
    archive_manifest = []
    for index, quarter in enumerate(quarters):
        rows, metadata = _download_quarter(session, quarter, output_dir)
        all_rows.extend(rows)
        archive_manifest.append(metadata)
        print(
            f"{quarter}: total={len(rows)} P={metadata['nport_p']} "
            f"PA={metadata['nport_p_a']} CIK={metadata['distinct_registrant_ciks']}",
            flush=True,
        )
        if index + 1 < len(quarters):
            time.sleep(0.25)

    accessions = [x["accession"] for x in all_rows]
    if len(accessions) != len(set(accessions)):
        raise RuntimeError("duplicate_accession_across_quarters")
    if not all_rows:
        raise RuntimeError("zero_target_accessions_across_full_history")

    sample = select_stratified_sample(all_rows)
    quarter_summary = []
    for q in quarters:
        items = [x for x in all_rows if x["quarter"] == q]
        quarter_summary.append({
            "quarter": q,
            "nport_p": sum(1 for x in items if x["form_type"] == "NPORT-P"),
            "nport_p_a": sum(1 for x in items if x["form_type"] == "NPORT-P/A"),
            "total_accessions": len(items),
            "distinct_registrant_ciks": len({x["cik"] for x in items}),
            "filing_date_min": min((x["filing_date"] for x in items), default=None),
            "filing_date_max": max((x["filing_date"] for x in items), default=None),
        })

    form_counts = Counter(x["form_type"] for x in all_rows)
    result = {
        "phase": 311,
        "status": "PASS_HISTORICAL_ACCESSION_CENSUS" if len(archive_manifest) == len(quarters) else "PARTIAL",
        "audit_start_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "coverage": {
            "start_quarter": start,
            "end_quarter": end,
            "expected_quarters": len(quarters),
            "retrieved_quarters": len(archive_manifest),
            "all_quarters_retrieved": len(archive_manifest) == len(quarters),
            "unique_accessions": len(all_rows),
            "nport_p": form_counts.get("NPORT-P", 0),
            "nport_p_a": form_counts.get("NPORT-P/A", 0),
            "distinct_registrant_ciks": len({x["cik"] for x in all_rows}),
            "filing_date_min": min(x["filing_date"] for x in all_rows),
            "filing_date_max": max(x["filing_date"] for x in all_rows),
            "duplicate_accessions": 0,
            "exact_form_filter": sorted(TARGET_FORMS),
        },
        "sample": {
            "design": "deterministic SHA-256 minimum per quarter and exact form; QA only, not representative",
            "candidate_count": len(sample),
            "candidates": sample,
        },
        "source": {
            "sec_nport_data_sets": DATASET_URL,
            "sec_nport_readme": README_URL,
            "sec_quarterly_master_index_pattern": f"{BASE_URL}/{{year}}/QTR{{quarter}}/master.zip",
            "historical_data_set_window": "October 2019 through September 2026",
            "public_disclosure_only": True,
            "quarterly_dataset_posting": True,
            "dataset_includes_as_filed_amendments": True,
        },
        "archive_manifest": archive_manifest,
        "controls": {
            "filing_date_is_first_public_timestamp": False,
            "acceptance_is_first_public_timestamp": False,
            "strict_pit_admitted": False,
            "series_identity_complete": False,
            "effective_dated_security_master_complete": False,
            "f80_universe_coverage_measured": False,
            "representative_sample": False,
            "return_test_run": False,
            "alpha_test_authorized": False,
            "bootstrap_loo_run": False,
            "chronological_oos_run": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "data_purchase": False,
            "vendor_contact": False,
            "email_sent": False,
        },
        "decision": (
            "Accession inventory only. Use filing date and acceptance metadata as filing clocks, "
            "not exact first-public timestamps. Preserve every NPORT-P and NPORT-P/A accession as "
            "a separate as-filed vintage. Do not infer that a fund position is a trade or informed "
            "signal. Next gates are raw filing sample reconciliation, amendment lineage, series "
            "identity, effective-dated security crosswalk and F80 universe coverage."
        ),
    }

    census_fields = ["quarter", "accession", "cik", "company_name", "form_type", "filing_date", "filename"]
    sample_fields = census_fields + ["sample_rule", "sample_group_size"]
    write_csv(output_dir / "nport_accession_census.csv", all_rows, census_fields)
    write_csv(output_dir / "nport_quarter_summary.csv", quarter_summary, [
        "quarter", "nport_p", "nport_p_a", "total_accessions",
        "distinct_registrant_ciks", "filing_date_min", "filing_date_max",
    ])
    write_csv(output_dir / "nport_stratified_sample_candidates.csv", sample, sample_fields)
    (output_dir / "nport_archive_manifest.json").write_text(
        json.dumps(archive_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase311_nport_accession_census_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2019Q4")
    parser.add_argument("--end", default="2026Q3")
    parser.add_argument("--output-dir", type=Path, default=Path("phase311_output"))
    args = parser.parse_args()
    try:
        result = run_census(args.start, args.end, args.output_dir, os.environ.get("SEC_CONTACT_EMAIL", ""))
    except Exception as exc:
        print(f"PHASE311_FAIL={type(exc).__name__}:{exc}", file=sys.stderr, flush=True)
        raise
    print(json.dumps({
        "phase": 311,
        "status": result["status"],
        "coverage": result["coverage"],
        "sample_candidate_count": result["sample"]["candidate_count"],
        "output_dir": str(args.output_dir),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
