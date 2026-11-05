#!/usr/bin/env python3
"""Phase 47 — SEC 13F accession-level PIT join audit.

Data gate only. Join SUBMISSION -> INFOTABLE by ACCESSION_NUMBER so every
holding row inherits the filing manager, report date and filing date. This
verifies that the structured datasets can support a point-in-time holdings
panel before any ticker/CUSIP crosswalk or alpha test.
"""
from __future__ import annotations

import csv, io, json, re, urllib.request, zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

DATASETS = {
    "2018_q1": "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip",
    "2026_jun_jul_aug": "https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip",
}

def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "NuevaEstrategia research audit contact research@example.com"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())

def parse_tsv(z: zipfile.ZipFile, name: str) -> tuple[list[str], list[list[str]]]:
    with z.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.reader(text, delimiter="\t")
        header = [x.strip() for x in next(reader)]
        rows = [row for row in reader if row]
    return header, rows

def idx(header: list[str], *names: str) -> int | None:
    m = {norm(x): i for i, x in enumerate(header)}
    return next((m[norm(x)] for x in names if norm(x) in m), None)

def main() -> None:
    out = {"phase": "47", "status": "UNKNOWN", "generated_utc": datetime.now().astimezone().isoformat(), "datasets": {}}
    all_ok = True
    for label, url in DATASETS.items():
        payload = download(url)
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            sub_name = next(n for n in z.namelist() if n.upper().endswith("SUBMISSION.TSV"))
            info_name = next(n for n in z.namelist() if n.upper().endswith("INFOTABLE.TSV"))
            sh, sr = parse_tsv(z, sub_name)
            ih, ir = parse_tsv(z, info_name)
        si = {"accession": idx(sh, "ACCESSION_NUMBER"), "cik": idx(sh, "CIK"), "report": idx(sh, "PERIODOFREPORT"), "filing": idx(sh, "FILING_DATE")}
        ii = {"accession": idx(ih, "ACCESSION_NUMBER"), "cusip": idx(ih, "CUSIP"), "figi": idx(ih, "FIGI"), "issuer": idx(ih, "NAMEOFISSUER"), "value": idx(ih, "VALUE"), "shares": idx(ih, "SSHPRNAMT"), "putcall": idx(ih, "PUTCALL"), "discretion": idx(ih, "INVESTMENTDISCRETION")}
        ok_schema = all(v is not None for v in si.values()) and all(ii[k] is not None for k in ("accession", "cusip", "value", "shares"))
        sub = {}
        for row in sr:
            a = row[si["accession"]].strip() if si["accession"] < len(row) else ""
            if not a: continue
            sub[a] = {"cik": row[si["cik"]].strip(), "report": row[si["report"]].strip(), "filing": row[si["filing"]].strip()}
        joined = 0; missing_accession = 0; bad_dates = 0; lag_values = []; unique_cusips = set(); unique_figi = set(); unique_ciks = set(); accession_counts = Counter(); nonpositive_value = 0; missing_cusip = 0
        sample_unmatched = []
        for row in ir:
            a = row[ii["accession"]].strip() if ii["accession"] < len(row) else ""
            accession_counts[a] += 1
            if not a or a not in sub:
                missing_accession += 1
                if len(sample_unmatched) < 10: sample_unmatched.append(a)
                continue
            joined += 1
            meta = sub[a]
            unique_ciks.add(meta["cik"])
            c = row[ii["cusip"]].strip() if ii["cusip"] < len(row) else ""
            if not c: missing_cusip += 1
            else: unique_cusips.add(c)
            if ii["figi"] is not None and ii["figi"] < len(row) and row[ii["figi"]].strip(): unique_figi.add(row[ii["figi"]].strip())
            try:
                r = datetime.strptime(meta["report"], "%d-%b-%Y").date()
                f = datetime.strptime(meta["filing"], "%d-%b-%Y").date()
                lag_values.append((f-r).days)
                if f < r: bad_dates += 1
            except Exception:
                bad_dates += 1
            try:
                if float(row[ii["value"]]) < 0: nonpositive_value += 1
            except Exception:
                pass
        multi_accessions = sum(1 for n in accession_counts.values() if n > 1)
        duplicate_rows = sum(n-1 for n in accession_counts.values() if n > 1)
        lag_sorted = sorted(lag_values)
        def pct(q): return lag_sorted[min(len(lag_sorted)-1, int(q*(len(lag_sorted)-1)))] if lag_sorted else None
        stats = {
            "submission_rows": len(sr), "infotable_rows": len(ir), "submission_accessions": len(sub),
            "joined_rows": joined, "join_rate": joined/len(ir) if ir else 0.0,
            "missing_accession_rows": missing_accession, "sample_unmatched_accessions": sample_unmatched,
            "unique_ciks": len(unique_ciks), "unique_cusips": len(unique_cusips), "unique_figi": len(unique_figi),
            "missing_cusip_rows": missing_cusip, "negative_value_rows": nonpositive_value,
            "accessions_with_multiple_holdings": multi_accessions, "extra_rows_beyond_one_per_accession": duplicate_rows,
            "filing_lag_days": {"min": min(lag_sorted) if lag_sorted else None, "p25": pct(.25), "median": pct(.5), "p75": pct(.75), "max": max(lag_sorted) if lag_sorted else None},
            "filing_before_report_rows": bad_dates,
        }
        out["datasets"][label] = {"schema": {"submission": si, "infotable": ii}, "schema_ok": ok_schema, "stats": stats}
        all_ok &= ok_schema and missing_accession == 0 and bad_dates == 0 and missing_cusip == 0 and nonpositive_value == 0
    out["status"] = "PASS_PIT_ACCESSION_JOIN" if all_ok else "FAIL_PIT_ACCESSION_JOIN"
    out["interpretation"] = "PIT panel integrity only; no alpha, no universe substitution, no production changes."
    out["next_gate"] = "Build a reproducible historical CUSIP/FIGI-to-F80 security crosswalk and quantify active-universe coverage by filing date."
    Path("sec_13f_pit_accession_join_audit.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__": main()
