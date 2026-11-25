#!/usr/bin/env python3
"""Phase 606 — bounded live audit of SEC 13F manager relationship TSVs.

Downloads only the public 2018 Q1 and 2026 Jun-Aug SEC 13F datasets.
Measures actual OTHERMANAGER / OTHERMANAGER2 cardinality, sequence references,
summary-page reconciliation and identifier resolution. No holdings signal or
return calculation is produced.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from research.sec_user_agent import resolve_sec_user_agent
except ModuleNotFoundError:
    from sec_user_agent import resolve_sec_user_agent

DATASETS = {
    "2018_q1": "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2018q1_form13f.zip",
    "2026_jun_jul_aug": "https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip",
}


def norm(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def index(header: list[str], *names: str) -> int | None:
    positions = {norm(value): i for i, value in enumerate(header)}
    return next((positions[norm(name)] for name in names if norm(name) in positions), None)


def cell(row: list[str], ix: int | None) -> str:
    return str(row[ix] or "").strip() if ix is not None and ix < len(row) else ""


def normalize_cik(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits or len(digits) > 10:
        return None
    return digits.zfill(10)


def normalize_file_number(value: object) -> str | None:
    raw = re.sub(r"\s+", "", str(value or "").strip())
    if not raw:
        return None
    match = re.fullmatch(r"0*28-0*(\d{1,8})", raw)
    return "028-" + match.group(1).zfill(5) if match else None


def resolve_manager_identity(cik_raw: object, file_raw: object,
                             file_number_to_ciks: dict[str, set[str]]) -> str:
    cik = normalize_cik(cik_raw)
    file_number = normalize_file_number(file_raw)
    candidates = file_number_to_ciks.get(file_number, set()) if file_number else set()
    if cik:
        if len(candidates) == 1 and cik not in candidates:
            return "IDENTITY_CONFLICT"
        return "EXPLICIT_CIK"
    if file_number and len(candidates) == 1:
        return "RESOLVED_BY_FILE_NUMBER"
    if file_number and len(candidates) > 1:
        return "AMBIGUOUS_FILE_NUMBER"
    if file_raw and not file_number:
        return "INVALID_FILE_NUMBER"
    return "UNRESOLVED_NO_IDENTIFIER"


def find_member(names: list[str], suffix: str) -> str:
    target = norm(suffix)
    matches = [name for name in names if norm(Path(name).name).endswith(target + "TSV")]
    if len(matches) != 1:
        raise ValueError(f"expected_one_{suffix}_tsv_found_{len(matches)}")
    return matches[0]


def read_table(archive: zipfile.ZipFile, member: str) -> tuple[list[str], list[list[str]]]:
    with archive.open(member) as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""), delimiter="\t")
        header = next(reader, [])
        rows = [row for row in reader if row]
    return [x.strip() for x in header], rows


def build_filer_context(submission_header: list[str], submission_rows: list[list[str]],
                        cover_header: list[str], cover_rows: list[list[str]]) -> dict:
    si = {
        "accession": index(submission_header, "ACCESSION_NUMBER"),
        "cik": index(submission_header, "CIK"),
        "form": index(submission_header, "SUBMISSIONTYPE", "SUBMISSION_TYPE"),
        "filing_date": index(submission_header, "FILING_DATE"),
        "report_period": index(submission_header, "PERIODOFREPORT", "PERIOD_OF_REPORT"),
    }
    ci = {
        "accession": index(cover_header, "ACCESSION_NUMBER"),
        "file_number": index(cover_header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "report_type": index(cover_header, "REPORTTYPE", "REPORT_TYPE"),
    }
    if any(v is None for v in si.values()) or any(v is None for v in ci.values()):
        return {"schema_ok": False, "missing_submission": [k for k,v in si.items() if v is None],
                "missing_coverpage": [k for k,v in ci.items() if v is None]}
    submissions = {}
    duplicate_submission = 0
    for row in submission_rows:
        accession = cell(row, si["accession"])
        if not accession:
            continue
        if accession in submissions:
            duplicate_submission += 1
            continue
        submissions[accession] = {
            "cik": normalize_cik(cell(row, si["cik"])),
            "submission_type": cell(row, si["form"]).upper(),
            "filing_date": cell(row, si["filing_date"]),
            "report_period": cell(row, si["report_period"]),
        }
    cover = {}
    duplicate_cover = 0
    for row in cover_rows:
        accession = cell(row, ci["accession"])
        if not accession:
            continue
        if accession in cover:
            duplicate_cover += 1
            continue
        cover[accession] = {
            "file_number": normalize_file_number(cell(row, ci["file_number"])),
            "file_number_raw": cell(row, ci["file_number"]),
            "report_type": cell(row, ci["report_type"]).upper(),
        }
    file_number_to_ciks: dict[str, set[str]] = defaultdict(set)
    filers = {}
    for accession, submission in submissions.items():
        cp = cover.get(accession)
        if cp is None:
            continue
        filer = {**submission, **cp}
        filers[accession] = filer
        if cp["file_number"] and submission["cik"]:
            file_number_to_ciks[cp["file_number"]].add(submission["cik"])
    return {
        "schema_ok": True,
        "filers": filers,
        "file_number_to_ciks": file_number_to_ciks,
        "submission_count": len(submissions),
        "coverpage_count": len(cover),
        "missing_coverpage": len(set(submissions) - set(cover)),
        "extra_coverpage": len(set(cover) - set(submissions)),
        "duplicate_submission_accessions": duplicate_submission,
        "duplicate_coverpage_accessions": duplicate_cover,
        "submission_type_counts": dict(sorted(Counter(x["submission_type"] for x in submissions.values()).items())),
        "report_type_counts": dict(sorted(Counter(x["report_type"] for x in cover.values()).items())),
    }


def audit_othermanager(header: list[str], rows: list[list[str]], filers: dict,
                       file_number_to_ciks: dict[str, set[str]]) -> dict:
    ix = {
        "accession": index(header, "ACCESSION_NUMBER"),
        "key": index(header, "OTHERMANAGER_SK", "OTHER_MANAGER_SK"),
        "cik": index(header, "CIK"),
        "file_number": index(header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "name": index(header, "NAME"),
    }
    missing = [k for k,v in ix.items() if v is None]
    if missing:
        return {"schema_ok": False, "missing_fields": missing, "rows": len(rows)}
    seen = set()
    counts = Counter()
    status = Counter()
    duplicate_keys = blank_accessions = orphan_accessions = invalid_keys = 0
    samples = []
    for row in rows:
        accession, key = cell(row, ix["accession"]), cell(row, ix["key"])
        if not accession:
            blank_accessions += 1
            continue
        counts[accession] += 1
        if not key.isdigit():
            invalid_keys += 1
            continue
        pair = (accession, key)
        if pair in seen:
            duplicate_keys += 1
        seen.add(pair)
        if accession not in filers:
            orphan_accessions += 1
        status[resolve_manager_identity(cell(row, ix["cik"]), cell(row, ix["file_number"]), file_number_to_ciks)] += 1
        if len(samples) < 8:
            samples.append({"accession": accession, "othermanager_sk": key})
    return {
        "schema_ok": True, "rows": len(rows), "unique_accessions": len(counts),
        "accessions_with_multiple_rows": sum(v > 1 for v in counts.values()),
        "max_rows_per_accession": max(counts.values(), default=0),
        "duplicate_accession_sk_keys": duplicate_keys, "blank_accessions": blank_accessions,
        "invalid_surrogate_keys": invalid_keys, "orphan_accessions": orphan_accessions,
        "identity_resolution": dict(sorted(status.items())), "sample_keys": samples,
        "rows_by_accession": dict(counts),
    }


def audit_othermanager2(header: list[str], rows: list[list[str]], filers: dict,
                        file_number_to_ciks: dict[str, set[str]]) -> dict:
    ix = {
        "accession": index(header, "ACCESSION_NUMBER"),
        "sequence": index(header, "SEQUENCENUMBER", "SEQUENCE_NUMBER"),
        "cik": index(header, "CIK"),
        "file_number": index(header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "name": index(header, "NAME"),
    }
    missing = [k for k,v in ix.items() if v is None]
    if missing:
        return {"schema_ok": False, "missing_fields": missing, "rows": len(rows)}
    seen_pairs = set()
    counts = Counter()
    sequences: dict[str, set[str]] = defaultdict(set)
    status = Counter()
    duplicate_pairs = blank_accessions = orphan_accessions = invalid_sequences = 0
    samples = []
    for row in rows:
        accession = cell(row, ix["accession"])
        raw_sequence = cell(row, ix["sequence"])
        if not accession:
            blank_accessions += 1
            continue
        counts[accession] += 1
        try:
            sequence = int(raw_sequence)
            if sequence < 1:
                raise ValueError
        except ValueError:
            invalid_sequences += 1
            continue
        pair = (accession, str(sequence))
        if pair in seen_pairs:
            duplicate_pairs += 1
        seen_pairs.add(pair)
        sequences[accession].add(str(sequence))
        if accession not in filers:
            orphan_accessions += 1
        status[resolve_manager_identity(cell(row, ix["cik"]), cell(row, ix["file_number"]), file_number_to_ciks)] += 1
        if len(samples) < 12:
            samples.append({"accession": accession, "sequence_number": sequence,
                            "manager_cik_raw": cell(row, ix["cik"]),
                            "file_number_raw": cell(row, ix["file_number"]),
                            "name_as_filed": cell(row, ix["name"])})
    multi = {k:v for k,v in counts.items() if v > 1}
    return {
        "schema_ok": True, "rows": len(rows), "unique_accessions": len(counts),
        "accession_only_key_collisions": sum(v - 1 for v in counts.values() if v > 1),
        "accessions_with_multiple_rows": len(multi), "max_rows_per_accession": max(counts.values(), default=0),
        "duplicate_accession_sequence_pairs": duplicate_pairs, "invalid_sequences": invalid_sequences,
        "blank_accessions": blank_accessions, "orphan_accessions": orphan_accessions,
        "identity_resolution": dict(sorted(status.items())), "sample_rows": samples,
        "rows_by_accession": dict(counts), "sequences_by_accession": {k: sorted(v, key=int) for k,v in sequences.items()},
    }


def audit_infotable_references(header: list[str], rows, filers: dict,
                               included_sequences: dict[str, set[str]]) -> dict:
    accession_ix = index(header, "ACCESSION_NUMBER")
    line_ix = index(header, "INFOTABLE_SK", "INFO_TABLE_SK")
    manager_ix = index(header, "OTHERMANAGER", "OTHER_MANAGER")
    missing = [name for name,ix in (("ACCESSION_NUMBER",accession_ix),("INFOTABLE_SK",line_ix),("OTHERMANAGER",manager_ix)) if ix is None]
    if missing:
        return {"schema_ok": False, "missing_fields": missing}
    total = joined = missing_accession = rows_with_refs = tokens = resolved = dangling = malformed = notice_rows = 0
    dangling_sample, malformed_sample = [], []
    notice_accessions = {a for a,f in filers.items()
                         if f["submission_type"] in {"13F-NT","13F-NT/A"} or f["report_type"] == "13F NOTICE"}
    for row in rows:
        total += 1
        accession = cell(row, accession_ix)
        if not accession or accession not in filers:
            missing_accession += 1
            continue
        joined += 1
        if accession in notice_accessions:
            notice_rows += 1
        raw = cell(row, manager_ix)
        if not raw or raw.upper() in {"N/A","NA","NONE"}:
            continue
        rows_with_refs += 1
        for token in raw.split(","):
            token = token.strip()
            if not token.isdigit() or int(token) < 1:
                malformed += 1
                if len(malformed_sample) < 8:
                    malformed_sample.append({"accession": accession, "line": cell(row,line_ix), "token": token})
                continue
            tokens += 1
            if token in included_sequences.get(accession, set()):
                resolved += 1
            else:
                dangling += 1
                if len(dangling_sample) < 8:
                    dangling_sample.append({"accession": accession, "line": cell(row,line_ix), "sequence": int(token)})
    return {
        "schema_ok": True, "rows": total, "joined_rows": joined,
        "missing_or_orphan_accession_rows": missing_accession, "rows_with_manager_refs": rows_with_refs,
        "manager_reference_tokens": tokens, "resolved_sequence_tokens": resolved,
        "dangling_sequence_tokens": dangling, "malformed_sequence_tokens": malformed,
        "notice_accession_holding_rows": notice_rows,
        "sample_dangling": dangling_sample, "sample_malformed": malformed_sample,
    }


def audit_summarypage(header: list[str], rows: list[list[str]], othermanager2_counts: dict[str,int]) -> dict:
    acc_ix = index(header, "ACCESSION_NUMBER")
    count_ix = index(header, "OTHERINCLUDEDMANAGERSCOUNT", "OTHER_INCLUDED_MANAGERS_COUNT")
    if acc_ix is None or count_ix is None:
        return {"schema_ok": False, "missing_fields": [k for k,v in (("ACCESSION_NUMBER",acc_ix),("OTHERINCLUDEDMANAGERSCOUNT",count_ix)) if v is None]}
    compared = mismatches = missing_values = 0
    sample = []
    for row in rows:
        accession = cell(row, acc_ix)
        raw = cell(row, count_ix)
        if not raw:
            missing_values += 1
            continue
        try:
            expected = int(raw)
        except ValueError:
            missing_values += 1
            continue
        actual = othermanager2_counts.get(accession, 0)
        compared += 1
        if expected != actual:
            mismatches += 1
            if len(sample) < 10:
                sample.append({"accession": accession, "summary_declared": expected, "othermanager2_rows": actual})
    return {"schema_ok": True, "rows": len(rows), "compared_rows": compared,
            "missing_or_invalid_counts": missing_values, "count_mismatches": mismatches,
            "sample_mismatches": sample}


def download(url: str, user_agent: str) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/zip,application/octet-stream,*/*",
    })
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def audit_infotable_member(payload: bytes, member: str, filers: dict,
                            included_sequences: dict[str, set[str]]) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        with archive.open(member) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""), delimiter="\t")
            header = next(reader, [])
            return audit_infotable_references([x.strip() for x in header], reader, filers, included_sequences)


def audit_dataset(label: str, url: str, user_agent: str) -> dict:
    payload = download(url, user_agent)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        members = {key: find_member(names,key) for key in
                   ("SUBMISSION","COVERPAGE","OTHERMANAGER","OTHERMANAGER2","SUMMARYPAGE","INFOTABLE")}
        sub_h, sub_rows = read_table(archive, members["SUBMISSION"])
        cov_h, cov_rows = read_table(archive, members["COVERPAGE"])
        om_h, om_rows = read_table(archive, members["OTHERMANAGER"])
        om2_h, om2_rows = read_table(archive, members["OTHERMANAGER2"])
        sum_h, sum_rows = read_table(archive, members["SUMMARYPAGE"])
    context = build_filer_context(sub_h,sub_rows,cov_h,cov_rows)
    if not context.get("schema_ok"):
        return {"status":"BLOCKED_FILER_SCHEMA","sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload),"filer_context":context}
    filers, mapping = context["filers"], context["file_number_to_ciks"]
    om = audit_othermanager(om_h,om_rows,filers,mapping)
    om2 = audit_othermanager2(om2_h,om2_rows,filers,mapping)
    info = audit_infotable_member(payload,members["INFOTABLE"],filers,
        {k:set(v) for k,v in om2.get("sequences_by_accession",{}).items()})
    summary = audit_summarypage(sum_h,sum_rows,om2.get("rows_by_accession",{}))
    notices = {a for a,f in filers.items() if f["submission_type"] in {"13F-NT","13F-NT/A"} or f["report_type"] == "13F NOTICE"}
    notice_without_roster = [a for a in notices if om.get("rows_by_accession",{}).get(a,0)==0]
    required_ok = all(x.get("schema_ok") for x in (om,om2,info,summary))
    structural_ok = required_ok and om.get("duplicate_accession_sk_keys",0)==0 and om2.get("duplicate_accession_sequence_pairs",0)==0 and info.get("dangling_sequence_tokens",0)==0 and info.get("malformed_sequence_tokens",0)==0
    if om2.get("accessions_with_multiple_rows",0):
        key_interpretation = "ACCESSION_NUMBER-only key notation is not unique in observed rows; (ACCESSION_NUMBER, SEQUENCENUMBER) is a candidate logical key, subject to source-filing reconciliation."
    else:
        key_interpretation = "No multi-row OTHERMANAGER2 accession observed in this sample; the one-to-many sequence design remains untested."
    samples = []
    counts = om2.get("rows_by_accession",{})
    for accession in sorted(counts, key=lambda a:(-counts[a],a))[:10]:
        filer = filers.get(accession,{})
        samples.append({"accession":accession,"filer_cik":filer.get("cik"),
                        "submission_type":filer.get("submission_type"),"report_type":filer.get("report_type"),
                        "filing_date":filer.get("filing_date"),"report_period":filer.get("report_period"),
                        "othermanager2_rows":counts[accession],
                        "sequences":om2.get("sequences_by_accession",{}).get(accession,[])})
    return {
        "status":"PASS_STRUCTURAL_COUNTS" if structural_ok else "REVIEW_STRUCTURAL_OR_IDENTITY_EXCEPTIONS",
        "source_url":url,"zip_bytes":len(payload),"zip_sha256":hashlib.sha256(payload).hexdigest(),
        "members":members,"filer_context":{k:v for k,v in context.items() if k not in {"filers","file_number_to_ciks"}},
        "othermanager":{k:v for k,v in om.items() if k!="rows_by_accession"},
        "othermanager2":{k:v for k,v in om2.items() if k not in {"rows_by_accession","sequences_by_accession"}},
        "infotable_references":info,"summarypage_reconciliation":summary,
        "notice_controls":{"notice_accessions":len(notices),"notice_accessions_without_othermanager_roster":len(notice_without_roster),
                           "sample_without_roster":sorted(notice_without_roster)[:10]},
        "othermanager2_key_interpretation":key_interpretation,
        "largest_othermanager2_accessions_sample":samples,
        "signal_eligible":False,
    }


def main() -> None:
    user_agent, user_agent_source = resolve_sec_user_agent()
    out = {"phase":606,"generated_utc":datetime.now(timezone.utc).isoformat(),
           "user_agent_source":user_agent_source,"status":"UNKNOWN","datasets":{}}
    for label,url in DATASETS.items():
        try:
            out["datasets"][label] = audit_dataset(label,url,user_agent)
        except Exception as exc:
            out["datasets"][label] = {"status":"DOWNLOAD_OR_PARSE_ERROR","error_type":type(exc).__name__,"error":str(exc)[:500],"source_url":url}
    statuses = [v.get("status") for v in out["datasets"].values()]
    out["status"] = "PASS_STRUCTURAL_COUNTS" if statuses and all(s=="PASS_STRUCTURAL_COUNTS" for s in statuses) else "REVIEW_OR_BLOCKED"
    out["interpretation"] = (
        "Actual SEC table cardinality and cross-table reference audit only. "
        "No beneficial ownership, control, trade direction, information advantage, alpha, OOS, bootstrap, LOO or production eligibility is inferred."
    )
    out["next_gate"] = (
        "Reconcile a stratified set of OTHERMANAGER and OTHERMANAGER2 rows plus INFOTABLE sequence references against original EDGAR filing XML; "
        "then implement notice/combination amendment state as-of filing availability."
    )
    Path("phase606_sec_13f_manager_table_live_audit.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))


if __name__ == "__main__":
    main()
