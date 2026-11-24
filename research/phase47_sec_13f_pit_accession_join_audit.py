#!/usr/bin/env python3
"""Phase 47 — SEC 13F accession-level PIT and amendment audit.

Data gate only. Join SUBMISSION -> INFOTABLE by ACCESSION_NUMBER, retain the
manager/report/filing clocks and amendment semantics, and calculate filing
lags once per submission (not once per holding row). No alpha or production
changes are performed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from research.sec_user_agent import resolve_sec_user_agent

DATASETS = {
    "2018_q1": "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip",
    "2026_jun_jul_aug": "https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip",
}


def download(url: str, user_agent: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/zip,application/octet-stream,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def norm(value: str) -> str:
    import re
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def parse_tsv(archive: zipfile.ZipFile, name: str) -> tuple[list[str], list[list[str]]]:
    with archive.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.reader(text, delimiter="\t")
        header = [value.strip() for value in next(reader)]
        rows = [row for row in reader if row]
    return header, rows


def idx(header: list[str], *names: str) -> int | None:
    positions = {norm(value): i for i, value in enumerate(header)}
    return next((positions[norm(name)] for name in names if norm(name) in positions), None)


def distribution(values: list[int]) -> dict:
    ordered = sorted(values)

    def pct(q: float):
        return ordered[min(len(ordered) - 1, int(q * (len(ordered) - 1)))] if ordered else None

    return {
        "n_submissions": len(ordered),
        "min": min(ordered) if ordered else None,
        "p25": pct(0.25),
        "median": pct(0.50),
        "p75": pct(0.75),
        "max": max(ordered) if ordered else None,
    }


def build_submission_map(header: list[str], rows: list[list[str]]) -> tuple[dict, dict, bool]:
    si = {
        "accession": idx(header, "ACCESSION_NUMBER"),
        "filing": idx(header, "FILING_DATE"),
        "submission_type": idx(header, "SUBMISSIONTYPE", "SUBMISSION_TYPE"),
        "cik": idx(header, "CIK"),
        "report": idx(header, "PERIODOFREPORT", "PERIOD_OF_REPORT"),
        "amendment_number": idx(header, "AMENDMENT_NUMBER", "AMENDMENTNUMBER"),
        "amendment_type": idx(header, "AMENDMENTTYPE", "AMENDMENT_TYPE"),
    }
    schema_ok = all(si[key] is not None for key in si)
    if not schema_ok:
        return {}, {"schema": si, "invalid_dates": len(rows)}, False

    submissions = {}
    duplicate_accessions = 0
    type_counts = Counter()
    amendment_type_counts = Counter()
    amendment_rows = 0
    amendment_missing_number = 0
    amendment_missing_type = 0
    invalid_dates = 0
    filing_before_report = 0
    lags_by_type = defaultdict(list)
    manager_period_counts = Counter()

    for row in rows:
        accession = row[si["accession"]].strip() if si["accession"] < len(row) else ""
        if not accession:
            invalid_dates += 1
            continue
        if accession in submissions:
            duplicate_accessions += 1
            continue

        submission_type = row[si["submission_type"]].strip().upper()
        cik = row[si["cik"]].strip()
        report = row[si["report"]].strip()
        filing = row[si["filing"]].strip()
        amendment_number = row[si["amendment_number"]].strip()
        amendment_type = row[si["amendment_type"]].strip().upper()

        type_counts[submission_type or "<blank>"] += 1
        is_amendment = submission_type.endswith("/A")
        if is_amendment:
            amendment_rows += 1
            if not amendment_number:
                amendment_missing_number += 1
            if not amendment_type:
                amendment_missing_type += 1
            if amendment_type:
                amendment_type_counts[amendment_type] += 1

        lag_days = None
        try:
            report_date = datetime.strptime(report, "%d-%b-%Y").date()
            filing_date = datetime.strptime(filing, "%d-%b-%Y").date()
            lag_days = (filing_date - report_date).days
            if lag_days < 0:
                filing_before_report += 1
            lags_by_type[submission_type or "<blank>"].append(lag_days)
        except (TypeError, ValueError):
            invalid_dates += 1

        if cik and report:
            manager_period_counts[(cik, report)] += 1

        submissions[accession] = {
            "cik": cik,
            "report": report,
            "filing": filing,
            "submission_type": submission_type,
            "amendment_number": amendment_number,
            "amendment_type": amendment_type,
            "lag_days": lag_days,
        }

    multi_filing_manager_periods = sum(1 for count in manager_period_counts.values() if count > 1)
    stats = {
        "submission_rows": len(rows),
        "submission_accessions": len(submissions),
        "duplicate_accession_rows": duplicate_accessions,
        "submission_type_counts": dict(sorted(type_counts.items())),
        "amendment_rows": amendment_rows,
        "amendment_type_counts": dict(sorted(amendment_type_counts.items())),
        "amendment_missing_number_rows": amendment_missing_number,
        "amendment_missing_type_rows": amendment_missing_type,
        "manager_period_groups": len(manager_period_counts),
        "manager_period_groups_with_multiple_submissions": multi_filing_manager_periods,
        "filing_lag_days": distribution([v["lag_days"] for v in submissions.values() if v["lag_days"] is not None]),
        "filing_lag_days_by_submission_type": {
            key: distribution(values) for key, values in sorted(lags_by_type.items())
        },
        "invalid_date_or_accession_rows": invalid_dates,
        "filing_before_report_submissions": filing_before_report,
    }
    amendment_metadata_ok = amendment_missing_number == 0 and amendment_missing_type == 0
    return submissions, {"indices": si, "stats": stats}, amendment_metadata_ok


def audit_dataset(label: str, url: str, user_agent: str) -> tuple[dict, bool]:
    payload = download(url, user_agent)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        submission_name = next(name for name in archive.namelist() if name.upper().endswith("SUBMISSION.TSV"))
        infotable_name = next(name for name in archive.namelist() if name.upper().endswith("INFOTABLE.TSV"))
        submission_header, submission_rows = parse_tsv(archive, submission_name)
        infotable_header, infotable_rows = parse_tsv(archive, infotable_name)

    submissions, submission_meta, amendment_metadata_ok = build_submission_map(submission_header, submission_rows)
    si = submission_meta["indices"]
    ii = {
        "accession": idx(infotable_header, "ACCESSION_NUMBER"),
        "cusip": idx(infotable_header, "CUSIP"),
        "figi": idx(infotable_header, "FIGI"),
        "issuer": idx(infotable_header, "NAMEOFISSUER"),
        "value": idx(infotable_header, "VALUE"),
        "shares": idx(infotable_header, "SSHPRNAMT"),
        "putcall": idx(infotable_header, "PUTCALL"),
        "discretion": idx(infotable_header, "INVESTMENTDISCRETION"),
    }
    required_info = ("accession", "cusip", "value", "shares")
    info_schema_ok = all(ii[key] is not None for key in required_info)
    if not info_schema_ok or not submissions:
        return {
            "schema": {"submission": si, "infotable": ii},
            "schema_ok": False,
            "submission": submission_meta.get("stats", {}),
            "stats": {"infotable_rows": len(infotable_rows)},
        }, False

    joined = 0
    missing_accession = 0
    unique_cusips = set()
    unique_figi = set()
    unique_ciks = {meta["cik"] for meta in submissions.values() if meta["cik"]}
    accession_counts = Counter()
    nonpositive_value = 0
    missing_cusip = 0
    sample_unmatched = []

    for row in infotable_rows:
        accession = row[ii["accession"]].strip() if ii["accession"] < len(row) else ""
        accession_counts[accession] += 1
        if not accession or accession not in submissions:
            missing_accession += 1
            if len(sample_unmatched) < 10:
                sample_unmatched.append(accession)
            continue
        joined += 1
        cusip = row[ii["cusip"]].strip() if ii["cusip"] < len(row) else ""
        if not cusip:
            missing_cusip += 1
        else:
            unique_cusips.add(cusip)
        if ii["figi"] is not None and ii["figi"] < len(row) and row[ii["figi"]].strip():
            unique_figi.add(row[ii["figi"]].strip())
        try:
            if float(row[ii["value"]]) < 0:
                nonpositive_value += 1
        except (TypeError, ValueError):
            pass

    multi_accessions = sum(1 for count in accession_counts.values() if count > 1)
    duplicate_rows = sum(count - 1 for count in accession_counts.values() if count > 1)
    submission_stats = submission_meta["stats"]
    stats = {
        "submission_rows": submission_stats["submission_rows"],
        "submission_accessions": submission_stats["submission_accessions"],
        "infotable_rows": len(infotable_rows),
        "joined_rows": joined,
        "join_rate": joined / len(infotable_rows) if infotable_rows else 0.0,
        "missing_accession_rows": missing_accession,
        "sample_unmatched_accessions": sample_unmatched,
        "unique_ciks": len(unique_ciks),
        "unique_cusips": len(unique_cusips),
        "unique_figi": len(unique_figi),
        "missing_cusip_rows": missing_cusip,
        "negative_value_rows": nonpositive_value,
        "accessions_with_multiple_holdings": multi_accessions,
        "extra_rows_beyond_one_per_accession": duplicate_rows,
        **submission_stats,
    }
    ok = (
        info_schema_ok
        and missing_accession == 0
        and missing_cusip == 0
        and nonpositive_value == 0
        and submission_stats["duplicate_accession_rows"] == 0
        and submission_stats["invalid_date_or_accession_rows"] == 0
        and submission_stats["filing_before_report_submissions"] == 0
        and amendment_metadata_ok
    )
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "schema": {"submission": si, "infotable": ii},
        "schema_ok": info_schema_ok and all(value is not None for value in si.values()),
        "stats": stats,
        "clock_contract": {
            "source_clock": "FILING_DATE from SUBMISSION.tsv",
            "precision": "date_only; exact EDGAR acceptance timestamp is not included in this dataset table",
            "conservative_eligibility": "first full regular session strictly after FILING_DATE",
            "report_period_is_not_availability": True,
            "quarterly_dataset_publication_is_not_first_receipt": True,
        },
    }, ok


def main() -> None:
    user_agent, user_agent_source = resolve_sec_user_agent()
    out = {
        "phase": "47",
        "status": "UNKNOWN",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "user_agent_source": user_agent_source,
        "datasets": {},
    }
    all_ok = True
    for label, url in DATASETS.items():
        result, ok = audit_dataset(label, url, user_agent)
        out["datasets"][label] = result
        all_ok = all_ok and ok

    out["status"] = "PASS_PIT_JOIN_AND_AMENDMENT_METADATA" if all_ok else "FAIL_PIT_JOIN_OR_AMENDMENT_METADATA"
    out["interpretation"] = (
        "PIT accession join and amendment metadata integrity only. Filing date is date-only; "
        "no exact acceptance/public-first-receipt timestamp, historical F80 crosswalk, alpha, "
        "OOS, bootstrap, LOO or production change is established."
    )
    out["next_gate"] = (
        "Build date-appropriate CUSIP/FIGI-to-F80 identity coverage and an as-of filing-date "
        "amendment state machine: RESTATEMENT supersedes; NEW HOLDINGS ENTRIES supplements."
    )
    Path("sec_13f_pit_accession_join_audit.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
