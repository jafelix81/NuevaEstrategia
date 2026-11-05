#!/usr/bin/env python3
"""Phase 45 — SEC Form 13F historical feasibility audit.

Data gate only. No alpha test and no production/baseline changes.
Audits representative SEC public 13F datasets for structured schema, PIT
fields, and full-table filer/holding coverage. The audit deliberately stops
before any return test or universe substitution.
"""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

DATASETS = {
    "2018_q1": "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip",
    "2026_jun_jul_aug": "https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip",
}


def download(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "NuevaEstrategia research audit contact research@example.com"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def inspect_zip(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        files = [n for n in z.namelist() if not n.endswith("/")]
        tabular_files = [n for n in files if n.lower().endswith((".csv", ".tsv", ".txt"))]
        samples = []
        for name in tabular_files[:20]:
            raw = z.read(name)
            text = raw.decode("utf-8-sig", errors="replace")
            lines = [x for x in text.splitlines() if x.strip()]
            if not lines:
                continue
            first = lines[0]
            counts = {"\t": first.count("\t"), ",": first.count(","), "|": first.count("|")}
            delim = max(counts, key=counts.get)
            rows = list(csv.reader(lines[:3], delimiter=delim))
            header = [x.strip() for x in rows[0]] if rows else []
            samples.append({"file": name, "size_bytes": len(raw), "delimiter": delim, "columns": header[:80]})
        return {"file_count": len(files), "tabular_file_count": len(tabular_files), "files": files[:80], "samples": samples}


def semantic_columns(samples: list[dict]) -> dict:
    all_cols = []
    for s in samples:
        all_cols.extend(s.get("columns", []))
    n = {norm(x): x for x in all_cols}
    groups = {
        "identity": ["CUSIP", "CUSIPNO", "ISSUERNAME", "NAMEOFISSUER"],
        "position": ["VALUE", "SSHPRNAMT", "SHRSORPRNAMT", "SHARES", "PRNAMT"],
        "report_date": ["PERIODOFREPORT", "REPORTDATE", "REPORTPERIOD", "REPORTCALENDARORQUARTER"],
        "filing_date": ["FILINGDATE", "FILEDDATE", "ACCEPTEDDATE", "ACCEPTED"],
        "manager": ["CIK", "FILERCIK", "FILERNAME", "MANAGERNAME", "FILINGMANAGERNAME"],
    }
    return {k: [n[c] for c in candidates if c in n] for k, candidates in groups.items()}


def find_table(z: zipfile.ZipFile, preferred: tuple[str, ...]) -> str | None:
    names = [n for n in z.namelist() if not n.endswith("/")]
    for p in preferred:
        for n in names:
            if n.upper().endswith(p.upper()):
                return n
    return None


def read_tsv_stats(z: zipfile.ZipFile, name: str | None) -> dict:
    if not name:
        return {"present": False}
    with z.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.reader(text, delimiter="\t")
        try:
            header = [x.strip() for x in next(reader)]
        except StopIteration:
            return {"present": True, "rows": 0, "columns": []}
        idx = {norm(x): i for i, x in enumerate(header)}
        candidates = {
            "cik": ["CIK", "FILERCIK"],
            "cusip": ["CUSIP", "CUSIPNO"],
            "value": ["VALUE"],
            "shares": ["SSHPRNAMT", "SHRSORPRNAMT"],
            "report_date": ["PERIODOFREPORT", "REPORTDATE", "REPORTPERIOD"],
            "filing_date": ["FILINGDATE", "FILEDDATE", "ACCEPTEDDATE", "ACCEPTED"],
        }
        chosen = {k: next((idx[c] for c in cs if c in idx), None) for k, cs in candidates.items()}
        rows = 0
        unique_cik: set[str] = set()
        unique_cusip: set[str] = set()
        report_dates: set[str] = set()
        filing_dates: set[str] = set()
        missing = {k: 0 for k, v in chosen.items() if v is not None}
        for row in reader:
            if not row:
                continue
            rows += 1
            for k, j in chosen.items():
                if j is None or j >= len(row):
                    continue
                v = row[j].strip()
                if not v:
                    missing[k] += 1
                elif k == "cik":
                    unique_cik.add(v)
                elif k == "cusip":
                    unique_cusip.add(v)
                elif k == "report_date":
                    report_dates.add(v)
                elif k == "filing_date":
                    filing_dates.add(v)
        return {
            "present": True,
            "rows": rows,
            "columns": header[:100],
            "chosen_columns": chosen,
            "unique_cik": len(unique_cik),
            "unique_cusip": len(unique_cusip),
            "report_date_count": len(report_dates),
            "filing_date_count": len(filing_dates),
            "report_date_min": min(report_dates) if report_dates else None,
            "report_date_max": max(report_dates) if report_dates else None,
            "filing_date_min": min(filing_dates) if filing_dates else None,
            "filing_date_max": max(filing_dates) if filing_dates else None,
            "missing_counts": missing,
        }


def full_table_audit(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        info = {}
        submission = find_table(z, ("SUBMISSION.tsv", "SUBMISSION.TSV"))
        infotable = find_table(z, ("INFOTABLE.tsv", "INFOTABLE.TSV"))
        info["submission_file"] = submission
        info["infotable_file"] = infotable
        info["submission"] = read_tsv_stats(z, submission)
        info["infotable"] = read_tsv_stats(z, infotable)
        return info


def main() -> None:
    report = {
        "phase": "45",
        "status": "UNKNOWN",
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "datasets": {},
        "interpretation": "Data feasibility only; no alpha test and no production changes.",
    }
    for label, url in DATASETS.items():
        payload = download(url)
        info = inspect_zip(payload)
        info["download_bytes"] = len(payload)
        info["semantic_columns"] = semantic_columns(info["samples"])
        info["full_table_audit"] = full_table_audit(payload)
        report["datasets"][label] = info

    required = {"identity", "position", "report_date", "filing_date", "manager"}
    ok = True
    for d in report["datasets"].values():
        present = {k for k, v in d["semantic_columns"].items() if v}
        if not required.issubset(present):
            ok = False
        ft = d["full_table_audit"]
        if not ft.get("submission", {}).get("present") or not ft.get("infotable", {}).get("present"):
            ok = False
        if ft.get("infotable", {}).get("rows", 0) <= 0:
            ok = False

    report["status"] = "PASS_SOURCE_SCHEMA_PIT_FILER_HOLDINGS" if ok else "FAIL_SOURCE_SCHEMA_PIT_FILER_HOLDINGS"
    report["next_gate"] = (
        "Build a date-appropriate CUSIP crosswalk and quantify coverage against the historical investable universe. Do not substitute today's 335 symbols for the historical universe and do not run alpha until PIT universe coverage is demonstrated."
        if ok else
        "Stop before alpha; resolve missing filer/holding-table fields or source coverage first."
    )
    Path("sec_13f_feasibility_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
