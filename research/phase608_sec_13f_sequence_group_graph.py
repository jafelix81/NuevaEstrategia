#!/usr/bin/env python3
"""Phase 608 — group-aware SEC 13F OTHERMANAGER2 / INFOTABLE graph.

Sequence numbers identify groups. Multiple OTHERMANAGER2 member rows may share
one sequence number. INFOTABLE references the group, not an individual member.
Nonnumeric Other Manager values are preserved as raw filed text.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def norm_header(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def find_index(header: list[str], *candidates: str) -> int | None:
    positions = {norm_header(value): i for i, value in enumerate(header)}
    for candidate in candidates:
        if norm_header(candidate) in positions:
            return positions[norm_header(candidate)]
    return None


def cell(row: list[str], ix: int | None) -> str:
    return str(row[ix] or "").strip() if ix is not None and ix < len(row) else ""


def normalize_cik(value: str) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits or len(digits) > 10:
        return None
    return digits.zfill(10)


def normalize_file_number(value: str) -> str | None:
    raw = re.sub(r"\s+", "", str(value or "").strip())
    match = re.fullmatch(r"0*28-0*(\d{1,8})", raw)
    return "028-" + match.group(1).zfill(5) if match else None


def parse_manager_field(raw_value: object) -> dict:
    """Preserve nonnumeric filed text; parse only wholly numeric lists."""
    raw = str(raw_value or "").strip()
    if not raw or raw.upper() in {"N/A", "NA", "NONE"}:
        return {"status": "NO_REFERENCE", "raw_value": raw, "sequence_refs": [], "zero_count": 0}
    tokens = [x for x in re.split(r"[,\s]+", raw) if x]
    if not tokens:
        return {"status": "NO_REFERENCE", "raw_value": raw, "sequence_refs": [], "zero_count": 0}
    if not all(x.isdigit() for x in tokens):
        return {"status": "NONNUMERIC_AS_FILED", "raw_value": raw, "sequence_refs": [], "zero_count": 0}
    zeros = sum(int(x) == 0 for x in tokens)
    refs = [int(x) for x in tokens if int(x) > 0]
    if refs:
        return {"status": "NUMERIC_GROUP_REFS", "raw_value": raw, "sequence_refs": refs, "zero_count": zeros}
    return {"status": "ZERO_ONLY", "raw_value": raw, "sequence_refs": [], "zero_count": zeros}


def build_sequence_groups(header: list[str], rows: list[list[str]]) -> dict:
    ix = {
        "accession": find_index(header, "ACCESSION_NUMBER"),
        "sequence": find_index(header, "SEQUENCENUMBER", "SEQUENCE_NUMBER"),
        "cik": find_index(header, "CIK"),
        "file_number": find_index(header, "FORM13FFILENUMBER", "FORM_13F_FILE_NUMBER"),
        "crd": find_index(header, "CRDNUMBER", "CRD_NUMBER"),
        "sec_file": find_index(header, "SEC_FILENUMBER", "SEC_FILE_NUMBER"),
        "name": find_index(header, "NAME"),
    }
    missing = [k for k,v in ix.items() if v is None]
    if missing:
        raise ValueError("missing_othermanager2_fields:" + ",".join(missing))
    groups: dict[tuple[str,int], dict] = {}
    member_fingerprints = Counter()
    exact_duplicate_member_rows = 0
    invalid_member_rows = 0
    for row_ordinal, row in enumerate(rows, start=1):
        accession = cell(row, ix["accession"])
        if not accession:
            invalid_member_rows += 1
            continue
        raw_sequence = cell(row, ix["sequence"])
        try:
            sequence = int(raw_sequence)
            if sequence < 1:
                raise ValueError
        except ValueError:
            invalid_member_rows += 1
            continue
        cik = normalize_cik(cell(row, ix["cik"]))
        file_number = normalize_file_number(cell(row, ix["file_number"]))
        crd = cell(row, ix["crd"])
        sec_file = cell(row, ix["sec_file"])
        name = cell(row, ix["name"])
        fingerprint = (accession, sequence, cik or "", file_number or "", crd, sec_file, name)
        member_fingerprints[fingerprint] += 1
        if member_fingerprints[fingerprint] > 1:
            exact_duplicate_member_rows += 1
        # Row ordinal is deliberately included: identical as-filed rows are preserved,
        # not silently collapsed into one member.
        member_payload = "|".join([accession, str(sequence), cik or "", file_number or "", crd, sec_file, name, str(row_ordinal)])
        member_key = hashlib.sha256(member_payload.encode("utf-8")).hexdigest()[:20]
        if cik and file_number:
            identity_status = "CIK_AND_FILE_NUMBER"
        elif cik:
            identity_status = "CIK_ONLY"
        elif file_number:
            identity_status = "FILE_NUMBER_ONLY"
        else:
            identity_status = "NO_STABLE_IDENTIFIER"
        key = (accession, sequence)
        group = groups.setdefault(key, {
            "group_id": f"{accession}:{sequence}",
            "accession": accession,
            "sequence_number": sequence,
            "members": [],
        })
        group["members"].append({
            "member_key": member_key,
            "source_row_ordinal": row_ordinal,
            "cik": cik,
            "file_number": file_number,
            "crd_number": crd,
            "sec_file_number": sec_file,
            "name_as_filed": name,
            "identity_status": identity_status,
        })
    for group in groups.values():
        group["member_count"] = len(group["members"])
        group["member_attribution"] = "GROUP_ONLY" if group["member_count"] > 1 else "SINGLE_MEMBER_GROUP"
    return {
        "groups": groups,
        "audit": {
            "member_rows": sum(len(g["members"]) for g in groups.values()),
            "group_count": len(groups),
            "multi_member_groups": sum(g["member_count"] > 1 for g in groups.values()),
            "max_members_per_group": max((g["member_count"] for g in groups.values()), default=0),
            "exact_duplicate_member_rows": exact_duplicate_member_rows,
            "invalid_member_rows": invalid_member_rows,
        },
    }


def attach_infotable_rows(group_graph: dict, header: list[str], rows: list[list[str]]) -> dict:
    ix = {
        "accession": find_index(header, "ACCESSION_NUMBER"),
        "line": find_index(header, "INFOTABLE_SK", "INFO_TABLE_SK"),
        "manager": find_index(header, "OTHERMANAGER", "OTHER_MANAGER"),
    }
    missing = [k for k,v in ix.items() if v is None]
    if missing:
        raise ValueError("missing_infotable_fields:" + ",".join(missing))
    groups = group_graph["groups"]
    stats = Counter()
    links = []
    nonnumeric_labels = Counter()
    unmatched_examples = []
    for row in rows:
        accession = cell(row, ix["accession"])
        line_key = cell(row, ix["line"])
        parsed = parse_manager_field(cell(row, ix["manager"]))
        stats["infotable_rows"] += 1
        stats["zero_sentinel_count"] += parsed["zero_count"]
        if parsed["status"] == "NO_REFERENCE":
            stats["no_reference_rows"] += 1
        elif parsed["status"] == "ZERO_ONLY":
            stats["zero_only_rows"] += 1
        elif parsed["status"] == "NONNUMERIC_AS_FILED":
            stats["nonnumeric_as_filed_rows"] += 1
            nonnumeric_labels[parsed["raw_value"]] += 1
        elif parsed["status"] == "NUMERIC_GROUP_REFS":
            stats["numeric_reference_rows"] += 1
            for sequence in parsed["sequence_refs"]:
                stats["numeric_reference_tokens"] += 1
                group = groups.get((accession, sequence))
                if group is None:
                    stats["unmatched_sequence_tokens"] += 1
                    if len(unmatched_examples) < 12:
                        unmatched_examples.append({"accession": accession, "line": line_key, "sequence": sequence})
                    links.append({
                        "accession": accession, "line": line_key, "sequence_number": sequence,
                        "status": "UNMATCHED_SEQUENCE", "member_count": 0, "member_attribution": "NONE",
                    })
                else:
                    stats["matched_group_tokens"] += 1
                    if group["member_count"] > 1:
                        stats["group_only_reference_tokens"] += 1
                    else:
                        stats["single_member_group_tokens"] += 1
                    links.append({
                        "accession": accession, "line": line_key, "sequence_number": sequence,
                        "status": "MATCHED_GROUP", "group_id": group["group_id"],
                        "member_count": group["member_count"],
                        "member_attribution": group["member_attribution"],
                    })
    return {
        "audit": dict(stats),
        "nonnumeric_as_filed_values": dict(nonnumeric_labels.most_common(20)),
        "unmatched_examples": unmatched_examples,
        "links": links,
    }


def reconcile_summary_page(group_graph: dict, header: list[str], rows: list[list[str]]) -> dict:
    accession_ix = find_index(header, "ACCESSION_NUMBER")
    count_ix = find_index(header, "OTHERINCLUDEDMANAGERSCOUNT", "OTHER_INCLUDED_MANAGERS_COUNT")
    if accession_ix is None or count_ix is None:
        raise ValueError("missing_summarypage_accession_or_manager_count")
    member_counts = Counter()
    for group in group_graph["groups"].values():
        member_counts[group["accession"]] += group["member_count"]
    compared = mismatches = missing = 0
    samples = []
    for row in rows:
        accession = cell(row, accession_ix)
        raw_count = cell(row, count_ix)
        if not raw_count:
            missing += 1
            continue
        try:
            declared = int(raw_count)
        except ValueError:
            missing += 1
            continue
        compared += 1
        observed = member_counts.get(accession, 0)
        if declared != observed:
            mismatches += 1
            if len(samples) < 10:
                samples.append({"accession": accession, "declared_members": declared, "observed_members": observed})
    return {"compared": compared, "mismatches": mismatches, "missing_or_invalid": missing, "samples": samples}


def build_group_aware_graph(othermanager2_header: list[str], othermanager2_rows: list[list[str]],
                            infotable_header: list[str], infotable_rows: list[list[str]],
                            summary_header: list[str], summary_rows: list[list[str]]) -> dict:
    graph = build_sequence_groups(othermanager2_header, othermanager2_rows)
    info = attach_infotable_rows(graph, infotable_header, infotable_rows)
    summary = reconcile_summary_page(graph, summary_header, summary_rows)
    group_audit = graph["audit"]
    info_audit = info["audit"]
    result = {
        "status": "PASS_GROUP_STRUCTURE" if summary["mismatches"] == 0 and info_audit.get("unmatched_sequence_tokens", 0) == 0 else "REVIEW_GROUP_OR_REFERENCE_EXCEPTIONS",
        "group_audit": group_audit,
        "infotable_audit": info_audit,
        "summarypage_reconciliation": summary,
        "groups": sorted(graph["groups"].values(), key=lambda g:(g["accession"],g["sequence_number"])),
        "nonnumeric_as_filed_values": info["nonnumeric_as_filed_values"],
        "unmatched_examples": info["unmatched_examples"],
        "signal_eligible": False,
    }
    return result


def demo_fixture() -> dict:
    om_header = ["ACCESSION_NUMBER","SEQUENCENUMBER","CIK","FORM13FFILENUMBER","CRDNUMBER","SEC_FILENUMBER","NAME"]
    info_header = ["ACCESSION_NUMBER","INFOTABLE_SK","OTHERMANAGER"]
    summary_header = ["ACCESSION_NUMBER","OTHERINCLUDEDMANAGERSCOUNT"]
    om_rows = [
        ["ALLSPRING","1","0001327354","028-11406","000110841","801-58237","Allspring Funds Management, LLC"],
        ["ALLSPRING","1","","","","","Allspring Funds Management, LLC reporting on behalf of Morgan Stanley Smith Barney, LLC"],
        ["ALLSPRING","2","0001075869","028-04413","000104973","801-21122","Allspring Global Investments, LLC"],
        ["ALLSPRING","2","","","","","Allspring Global Investments, LLC reporting on behalf of SEI INVESTMENTS CO"],
        ["ALLSPRING","2","","","","","Allspring Global Investments, LLC reporting on behalf of UBS ASSET MANAGEMENT AMERICAS INC"],
    ]
    info_rows = [
        ["ALLSPRING","1","1"],["ALLSPRING","2","2"],["ALLSPRING","3","1,2"],
        ["XXEC","1","XXEC, INC."],["XXEC","2","XXEC, INC."],["XXEC","3","0"],
    ]
    summary_rows = [["ALLSPRING","5"],["XXEC","0"]]
    result = build_group_aware_graph(om_header,om_rows,info_header,info_rows,summary_header,summary_rows)
    result["fixture_note"] = "Synthetic structural fixture based on source-confirmed 2026 Allspring and XXEC filing patterns; not a live universe audit."
    return result


def main() -> None:
    result = demo_fixture()
    result["phase"] = 608
    result["generated_utc"] = datetime.now(timezone.utc).isoformat()
    result["interpretation"] = "Sequence groups are the attribution unit; member rows are preserved. No individual manager attribution is inferred for multi-member groups."
    Path("phase608_sec_13f_sequence_group_graph_demo.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
