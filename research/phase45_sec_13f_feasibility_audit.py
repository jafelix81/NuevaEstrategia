#!/usr/bin/env python3
"""Phase 45 — SEC Form 13F historical feasibility audit.

Data gate only. No alpha test and no production/baseline changes.
Audits representative SEC public 13F datasets for historical continuity,
structured schema, point-in-time fields and basic record coverage.

SEC changed the structured-data dataset URL family in 2026. The current
June-July-August 2026 release is used as the recent representative period.
"""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
import zipfile
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
        csv_files = [n for n in files if n.lower().endswith((".csv", ".txt"))]
        samples = []
        for name in csv_files[:20]:
            raw = z.read(name)
            text = raw.decode("utf-8-sig", errors="replace")
            lines = [x for x in text.splitlines() if x.strip()]
            if not lines:
                continue
            delim = "," if lines[0].count(",") >= lines[0].count("|") else "|"
            reader = csv.reader(lines[:3], delimiter=delim)
            rows = list(reader)
            header = [x.strip() for x in rows[0]] if rows else []
            samples.append({"file": name, "size_bytes": len(raw), "delimiter": delim, "columns": header[:80], "sample_rows": max(0, len(rows)-1)})
        return {"file_count": len(files), "csv_or_txt_count": len(csv_files), "files": files[:80], "samples": samples}


def semantic_columns(samples: list[dict]) -> dict:
    all_cols = []
    for s in samples:
        all_cols.extend(s.get("columns", []))
    n = {norm(x): x for x in all_cols}
    groups = {
        "identity": ["CUSIP", "CUSIPNO", "ISSUERNAME"],
        "position": ["VALUE", "SSHPRNAMT", "SHRSORPRNAMT", "SHARES", "PRNAMT"],
        "report_date": ["PERIODOFREPORT", "REPORTDATE", "REPORTPERIOD"],
        "filing_date": ["FILINGDATE", "FILEDDATE", "ACCEPTEDDATE", "ACCEPTED"],
        "manager": ["CIK", "FILERCIK", "FILERNAME", "MANAGERNAME"],
    }
    out = {}
    for k, candidates in groups.items():
        out[k] = [n[c] for c in candidates if c in n]
    return out


def main() -> None:
    report = {"phase": "45", "status": "UNKNOWN", "datasets": {}, "interpretation": "Data feasibility only."}
    for label, url in DATASETS.items():
        payload = download(url)
        info = inspect_zip(payload)
        info["download_bytes"] = len(payload)
        info["semantic_columns"] = semantic_columns(info["samples"])
        report["datasets"][label] = info

    required = {"identity", "position", "report_date", "filing_date", "manager"}
    ok = True
    for d in report["datasets"].values():
        present = {k for k, v in d["semantic_columns"].items() if v}
        if not required.issubset(present):
            ok = False
    report["status"] = "PASS_SOURCE_SCHEMA_PIT_FEASIBILITY" if ok else "FAIL_SOURCE_SCHEMA_PIT_FEASIBILITY"
    report["next_gate"] = (
        "Build filer-level point-in-time holdings panel using filing/acceptance date, map CUSIP to the frozen universe by date, and quantify universe coverage before any return test."
        if ok else
        "Inspect the dataset release/schema and stop before alpha; do not infer institutional behavior from an incomplete schema."
    )
    Path("sec_13f_feasibility_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
