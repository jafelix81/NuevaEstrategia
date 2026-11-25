#!/usr/bin/env python3
"""Phase 609 — full-quarter SEC 13F sequence-group audit for 2018 Q1 and 2026 Jun-Aug."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.sec_user_agent import resolve_sec_user_agent
from research.phase606_sec_13f_manager_table_live_audit import (
    DATASETS, download, find_member, read_table, build_filer_context, audit_othermanager,
)
from research.phase608_sec_13f_sequence_group_graph import (
    build_sequence_groups, parse_manager_field, reconcile_summary_page,
)


def cell(row: list[str], ix: int | None) -> str:
    return str(row[ix] or "").strip() if ix is not None and ix < len(row) else ""


def audit_infotable_rows(header: list[str], rows, filers: dict, groups: dict) -> dict:
    accession_ix = next((i for i,x in enumerate(header) if x.strip().upper().replace("_","")=="ACCESSIONNUMBER"),None)
    line_ix = next((i for i,x in enumerate(header) if x.strip().upper().replace("_","") in {"INFOTABLESK","INFOTABLESK"}),None)
    manager_ix = next((i for i,x in enumerate(header) if x.strip().upper().replace("_","")=="OTHERMANAGER"),None)
    if accession_ix is None or line_ix is None or manager_ix is None:
        raise ValueError("INFOTABLE required columns missing")
    notices = {a for a,f in filers.items()
               if f["submission_type"] in {"13F-NT","13F-NT/A"} or f["report_type"]=="13F NOTICE"}
    stats = Counter({
        "rows":0,"joined_rows":0,"orphan_or_missing_accession_rows":0,"notice_info_rows":0,
        "no_reference_rows":0,"zero_only_rows":0,"zero_sentinel_tokens":0,
        "nonnumeric_as_filed_rows":0,"numeric_reference_rows":0,"numeric_reference_tokens":0,
        "matched_group_tokens":0,"unmatched_sequence_tokens":0,
        "group_only_reference_tokens":0,"single_member_group_tokens":0,
    })
    nonnumeric = Counter()
    group_size_refs = Counter()
    unmatched_examples = []
    accessions = set()
    for row in rows:
        stats["rows"] += 1
        accession = cell(row,accession_ix)
        if not accession or accession not in filers:
            stats["orphan_or_missing_accession_rows"] += 1
            continue
        stats["joined_rows"] += 1
        accessions.add(accession)
        if accession in notices:
            stats["notice_info_rows"] += 1
        parsed = parse_manager_field(cell(row,manager_ix))
        stats["zero_sentinel_tokens"] += parsed["zero_count"]
        if parsed["status"] == "NO_REFERENCE":
            stats["no_reference_rows"] += 1
        elif parsed["status"] == "ZERO_ONLY":
            stats["zero_only_rows"] += 1
        elif parsed["status"] == "NONNUMERIC_AS_FILED":
            stats["nonnumeric_as_filed_rows"] += 1
            nonnumeric[parsed["raw_value"]] += 1
        elif parsed["status"] == "NUMERIC_GROUP_REFS":
            stats["numeric_reference_rows"] += 1
            for sequence in parsed["sequence_refs"]:
                stats["numeric_reference_tokens"] += 1
                group = groups.get((accession,sequence))
                if group is None:
                    stats["unmatched_sequence_tokens"] += 1
                    if len(unmatched_examples)<12:
                        unmatched_examples.append({"accession":accession,"line":cell(row,line_ix),"sequence":sequence})
                else:
                    stats["matched_group_tokens"] += 1
                    group_size_refs[group["member_count"]] += 1
                    if group["member_count"]>1:
                        stats["group_only_reference_tokens"] += 1
                    else:
                        stats["single_member_group_tokens"] += 1
    return {
        "audit":dict(stats),
        "unique_joined_accessions":len(accessions),
        "top_nonnumeric_as_filed_values":dict(nonnumeric.most_common(25)),
        "group_member_count_by_reference":dict(sorted(group_size_refs.items())),
        "unmatched_examples":unmatched_examples,
    }


def audit_dataset(label: str, url: str, user_agent: str) -> dict:
    payload = download(url,user_agent)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names=archive.namelist()
        members={k:find_member(names,k) for k in
                 ("SUBMISSION","COVERPAGE","OTHERMANAGER","OTHERMANAGER2","SUMMARYPAGE","INFOTABLE")}
        sub_h,sub_rows=read_table(archive,members["SUBMISSION"])
        cov_h,cov_rows=read_table(archive,members["COVERPAGE"])
        om_h,om_rows=read_table(archive,members["OTHERMANAGER"])
        om2_h,om2_rows=read_table(archive,members["OTHERMANAGER2"])
        sum_h,sum_rows=read_table(archive,members["SUMMARYPAGE"])
    context=build_filer_context(sub_h,sub_rows,cov_h,cov_rows)
    if not context.get("schema_ok"):
        return {"status":"BLOCKED_FILER_SCHEMA","zip_bytes":len(payload),"zip_sha256":hashlib.sha256(payload).hexdigest(),"filer_context":context}
    filers=context["filers"]
    om_audit=audit_othermanager(om_h,om_rows,filers,context["file_number_to_ciks"])
    graph=build_sequence_groups(om2_h,om2_rows)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        with archive.open(members["INFOTABLE"]) as raw:
            reader=csv.reader(io.TextIOWrapper(raw,encoding="utf-8-sig",errors="replace",newline=""),delimiter="\t")
            info_h=next(reader,[])
            info=audit_infotable_rows([x.strip() for x in info_h],reader,filers,graph["groups"])
    summary=reconcile_summary_page(graph,sum_h,sum_rows)
    notices={a for a,f in filers.items()
             if f["submission_type"] in {"13F-NT","13F-NT/A"} or f["report_type"]=="13F NOTICE"}
    othermanager_rows=om_audit.get("rows_by_accession",{})
    notice_without_roster=[a for a in notices if othermanager_rows.get(a,0)==0]
    identity=Counter(m["identity_status"] for g in graph["groups"].values() for m in g["members"])
    group_sizes=Counter(g["member_count"] for g in graph["groups"].values())
    info_audit=info["audit"]
    status="PASS_GROUP_STRUCTURE_WITH_DATA_EXCEPTIONS" if summary["mismatches"]==0 else "REVIEW_SUMMARYPAGE_MISMATCHES"
    return {
        "status":status,"source_url":url,"zip_bytes":len(payload),"zip_sha256":hashlib.sha256(payload).hexdigest(),
        "members":members,
        "filer_context":{k:v for k,v in context.items() if k not in {"filers","file_number_to_ciks"}},
        "othermanager":{"rows":om_audit.get("rows"),"unique_accessions":om_audit.get("unique_accessions"),
                        "duplicate_accession_sk_keys":om_audit.get("duplicate_accession_sk_keys"),
                        "identity_resolution":om_audit.get("identity_resolution")},
        "sequence_group_audit":{**graph["audit"],"identity_status_counts":dict(identity),
                                "group_size_distribution":dict(sorted(group_sizes.items()))},
        "infotable_group_reference_audit":info,
        "summarypage_reconciliation":summary,
        "notice_controls":{"notice_accessions":len(notices),
                           "notice_accessions_without_othermanager_roster":len(notice_without_roster),
                           "notice_info_rows":info_audit["notice_info_rows"],
                           "sample_without_roster":sorted(notice_without_roster)[:10]},
        "signal_eligible":False,
    }


def main() -> None:
    user_agent,source=resolve_sec_user_agent()
    out={"phase":609,"generated_utc":datetime.now(timezone.utc).isoformat(),
         "user_agent_source":source,"status":"UNKNOWN","datasets":{}}
    for label,url in DATASETS.items():
        try:
            out["datasets"][label]=audit_dataset(label,url,user_agent)
        except Exception as exc:
            out["datasets"][label]={"status":"DOWNLOAD_OR_PARSE_ERROR","error_type":type(exc).__name__,
                                    "error":str(exc)[:500],"source_url":url}
    statuses=[v.get("status") for v in out["datasets"].values()]
    out["status"]="PASS_FULL_QUARTER_GROUP_AUDIT" if statuses and all(s=="PASS_GROUP_STRUCTURE_WITH_DATA_EXCEPTIONS" for s in statuses) else "REVIEW_OR_BLOCKED"
    out["interpretation"]="Full-quarter group-structure and point-in-table reference audit only. No manager-level ownership, alpha, OOS, bootstrap, LOO or production eligibility."
    out["next_gate"]="Join group-level positions to effective-dated F80 securities and filing-acceptance timestamps; retain group ambiguity and unmatched references."
    Path("phase609_sec_13f_full_quarter_group_audit.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2))


if __name__=="__main__":
    main()
