#!/usr/bin/env python3
"""Phase 163: distinguish original filing anchors from immediate amendment parents."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PARENT_CASES = [
    {
        "previous_accession": "0000315066-12-002323",
        "parent_form": "SC 13G",
        "parent_filing_date": "2012-02-14",
        "parent_accepted_et": None,
        "parent_issuer_cik": "0001062579",
        "parent_issuer_name": "Amdocs Limited",
        "parent_cusip": "G02602103",
        "parent_source_url": "https://www.sec.gov/Archives/edgar/data/1062579/000031506612002323/0000315066-12-002323.txt",
        "children": [{
            "child_accession": "0000315066-26-000372",
            "child_form": "SC 13G/A",
            "child_amendment_no": 14,
            "child_issuer_cik": "0001062579",
            "child_cusip": "G02602103",
            "child_source_url": "https://www.sec.gov/Archives/edgar/data/1062579/000031506626000372/primary_doc.xml",
        }],
    },
    {
        "previous_accession": "0001274173-23-000077",
        "parent_form": "SC 13G",
        "parent_filing_date": "2023-02-14",
        "parent_accepted_et": "2023-02-14 16:51:19",
        "parent_issuer_cik": "0001785173",
        "parent_issuer_name": "89bio, Inc.",
        "parent_cusip": "282559103",
        "parent_source_url": "https://www.sec.gov/Archives/edgar/data/1785173/000127417323000077/89bio02142023.txt",
        "children": [{
            "child_accession": "0001274173-25-000015",
            "child_form": "SC 13G/A",
            "child_amendment_no": 5,
            "child_issuer_cik": "0001785173",
            "child_cusip": "282559103",
            "child_source_url": "https://www.sec.gov/Archives/edgar/data/1785173/000127417325000015/primary_doc.xml",
        }],
    },
    {
        "previous_accession": "0001644956-25-000024",
        "parent_form": "SC 13G",
        "parent_filing_date": "2025-05-09",
        "parent_accepted_et": "2025-05-09 16:13:10",
        "parent_issuer_cik": "0001643615",
        "parent_issuer_name": "Montrose Environmental Group, Inc.",
        "parent_cusip": "615111101",
        "parent_source_url": "https://www.sec.gov/Archives/edgar/data/1643615/000164495625000024/xslSCHEDULE_13G_X01/primary_doc.xml",
        "children": [{
            "child_accession": "0001644956-25-000034",
            "child_form": "SC 13G/A",
            "child_amendment_no": 1,
            "child_issuer_cik": "0001643615",
            "child_cusip": "615111101",
            "child_source_url": "https://www.sec.gov/Archives/edgar/data/1643615/000164495625000034/primary_doc.xml",
        }],
    },
    {
        "previous_accession": "0001193125-22-031137",
        "parent_form": "SC 13G",
        "parent_filing_date": "2022-02-08",
        "parent_accepted_et": "2022-02-08 17:11:01",
        "parent_issuer_cik": "0001766363",
        "parent_issuer_name": "Endeavor Group Holdings, Inc.",
        "parent_cusip": "29260Y109",
        "parent_source_url": "https://www.sec.gov/Archives/edgar/data/936828/000119312522031137/d284855dsc13g.htm",
        "children": [{
            "child_accession": "0001140361-25-017757",
            "child_form": "SC 13G/A",
            "child_amendment_no": None,
            "child_issuer_cik": "0001766363",
            "child_cusip": None,
            "child_source_url": "https://www.sec.gov/Archives/edgar/data/1766363/000114036125017757/primary_doc.xml",
        }],
    },
    {
        "previous_accession": "0001535610-24-000019",
        "parent_form": "SC 13G",
        "parent_filing_date": "2024-01-03",
        "parent_accepted_et": "2024-01-03 09:26:06",
        "parent_issuer_cik": "0001084267",
        "parent_issuer_name": "Mobiquity Technologies, Inc.",
        "parent_cusip": "60743F508",
        "parent_source_url": "https://www.sec.gov/Archives/edgar/data/1084267/000153561024000019/mobq0124.txt",
        "children": [{
            "child_accession": "0001535610-25-000004",
            "child_form": "SC 13G/A",
            "child_amendment_no": None,
            "child_issuer_cik": "0001084267",
            "child_cusip": None,
            "child_source_url": "https://www.sec.gov/Archives/edgar/data/1084267/000153561025000004/primary_doc.xml",
        }],
    },
    {
        "previous_accession": "0001445546-21-002430",
        "parent_form": "SC 13G",
        "parent_filing_date": "2021-05-10",
        "parent_accepted_et": "2021-05-10 09:06:41",
        "parent_issuer_cik": "0001667919",
        "parent_issuer_name": "First Trust Exchange-Traded Fund VIII",
        "parent_cusip": "33740F854",
        "parent_source_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554621002430/sc13g_3.txt",
        "children": [
            {"child_accession":"0001445546-25-002780","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0001667919","child_cusip":"33740F342","child_source_url":"https://www.sec.gov/Archives/edgar/data/1184765/000144554625002780/primary_doc.xml"},
            {"child_accession":"0001445546-25-002771","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0000904112","child_cusip":"617477104","child_source_url":"https://www.sec.gov/Archives/edgar/data/904112/000144554625002771/primary_doc.xml"},
            {"child_accession":"0001445546-25-002779","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0001667919","child_cusip":"33740F466","child_source_url":"https://www.sec.gov/Archives/edgar/data/1184765/000144554625002779/primary_doc.xml"},
            {"child_accession":"0001445546-25-004973","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0001667919","child_cusip":"33740F680","child_source_url":"https://www.sec.gov/Archives/edgar/data/1667919/000144554625004973/primary_doc.xml"},
            {"child_accession":"0001445546-26-007700","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0001667919","child_cusip":"33740U687","child_source_url":"https://www.sec.gov/Archives/edgar/data/1184765/000144554626007700/primary_doc.xml"},
            {"child_accession":"0001445546-26-008202","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0000779336","child_cusip":"003011111","child_source_url":"https://www.sec.gov/Archives/edgar/data/779336/000144554626008202/primary_doc.xml"},
            {"child_accession":"0001445546-26-008249","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0000908315","child_cusip":"974250102","child_source_url":"https://www.sec.gov/Archives/edgar/data/1184765/000144554626008249/primary_doc.xml"},
            {"child_accession":"0001445546-26-008161","child_form":"SC 13G/A","child_amendment_no":None,"child_issuer_cik":"0000855887","child_cusip":"09662E109","child_source_url":"https://www.sec.gov/Archives/edgar/data/1184765/000144554626008161/primary_doc.xml"},
        ],
    },
]


def normalize_accession(value: str) -> str | None:
    import re
    m = re.fullmatch(r"\s*(\d{1,10})-(\d{2})-(\d{1,6})\s*", str(value or ""))
    if not m:
        return None
    return f"{int(m.group(1)):010d}-{m.group(2)}-{int(m.group(3)):06d}"


def audit(cases: list[dict] | None = None) -> tuple[list[dict], dict]:
    cases = PARENT_CASES if cases is None else cases
    rows = []
    invalid = 0
    for case in cases:
        parent_accession = normalize_accession(case.get("previous_accession", ""))
        parent_issuer = str(case.get("parent_issuer_cik", "")).zfill(10)
        parent_cusip = str(case.get("parent_cusip", "")).strip()
        if not parent_accession or not parent_issuer.isdigit() or not parent_cusip:
            invalid += 1
            continue
        parent_is_initial = str(case.get("parent_form", "")).upper() in {"SC 13D", "SC 13G"}
        for child in case.get("children", []):
            child_accession = normalize_accession(child.get("child_accession", ""))
            child_issuer = str(child.get("child_issuer_cik", "")).zfill(10)
            child_cusip = str(child.get("child_cusip") or "").strip()
            if not child_accession or not child_issuer.isdigit():
                invalid += 1
                continue
            same_issuer = child_issuer == parent_issuer
            same_cusip = (child_cusip == parent_cusip) if child_cusip else None
            if not same_issuer:
                status = "CROSS_ISSUER_QUARANTINE"
            elif same_cusip is False:
                status = "SAME_ISSUER_DIFFERENT_CUSIP_QUARANTINE"
            elif same_cusip is True:
                status = "ISSUER_SECURITY_CONTINUITY_CANDIDATE_NOT_EDGE"
            else:
                status = "ISSUER_MATCH_SECURITY_UNVERIFIED"
            amendment_no = child.get("child_amendment_no")
            rows.append({
                "previous_accession": parent_accession,
                "parent_form": case["parent_form"],
                "parent_filing_date": case["parent_filing_date"],
                "parent_accepted_et": case.get("parent_accepted_et") or "",
                "parent_is_initial_filing": parent_is_initial,
                "parent_issuer_cik": parent_issuer,
                "parent_issuer_name": case["parent_issuer_name"],
                "parent_cusip": parent_cusip,
                "child_accession": child_accession,
                "child_form": child["child_form"],
                "child_amendment_no": amendment_no if amendment_no is not None else "",
                "child_issuer_cik": child_issuer,
                "child_cusip": child_cusip,
                "same_issuer_cik": same_issuer,
                "same_cusip": same_cusip,
                "status": status,
                "long_chain_anchor_evidence": bool(parent_is_initial and amendment_no and amendment_no > 1),
                "immediate_predecessor_verified": False,
                "parent_source_url": case["parent_source_url"],
                "child_source_url": child["child_source_url"],
            })

    first_trust = [r for r in rows if r["previous_accession"] == "0001445546-21-002430"]
    long_chain = [r for r in rows if r["long_chain_anchor_evidence"]]
    exact_candidates = [r for r in rows if r["status"] == "ISSUER_SECURITY_CONTINUITY_CANDIDATE_NOT_EDGE"]
    summary = {
        "phase": 163,
        "status": "COMPLETE_TARGETED_REFERENCE_SEMANTICS_AUDIT",
        "sample_design": "TARGETED_NON_RANDOM_DOCUMENT_LEVEL_CONTROLS",
        "phase160_unique_previous_accession_references": 32,
        "parent_documents_inspected": len(cases) - invalid,
        "unique_inspected_parent_accessions": len({r["previous_accession"] for r in rows}),
        "child_rows_examined": len(rows),
        "invalid_rows": invalid,
        "long_chain_initial_anchor_examples": len(long_chain),
        "issuer_security_continuity_candidates_not_edges": len(exact_candidates),
        "issuer_match_security_unverified": sum(r["status"] == "ISSUER_MATCH_SECURITY_UNVERIFIED" for r in rows),
        "cross_issuer_quarantines": sum(r["status"] == "CROSS_ISSUER_QUARANTINE" for r in rows),
        "same_issuer_different_cusip_quarantines": sum(r["status"] == "SAME_ISSUER_DIFFERENT_CUSIP_QUARANTINE" for r in rows),
        "first_trust_reused_reference_children": len(first_trust),
        "first_trust_exact_issuer_cusip_matches": sum(r["status"] == "ISSUER_SECURITY_CONTINUITY_CANDIDATE_NOT_EDGE" for r in first_trust),
        "uninspected_phase160_references": 32 - len({r["previous_accession"] for r in rows}),
        "immediate_predecessor_edges_verified": 0,
        "previous_accession_interpretation": "UNKNOWN_ORIGINAL_ANCHOR_OR_PREDECESSOR; empirical controls show it can point to the initial filing across multiple amendment numbers and can be reused across different securities/issuers",
        "decision": "Retain previousAccessionNumber as provenance/reference only. Do not create immediate-predecessor or ownership-state edges from the field alone. Require document-level issuer and effective-dated security continuity plus independent amendment-chain reconstruction.",
        "forward_returns_used": False,
        "final_holdout_used": False,
        "production_changed": False,
        "f80_changed": False,
    }
    return rows, summary


def write_outputs(rows: list[dict], summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase163_13dg_previous_accession_anchor_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    fields = list(rows[0].keys()) if rows else []
    with (output_dir / "phase163_13dg_previous_accession_anchor_rows.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    rows, summary = audit()
    write_outputs(rows, summary, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "COMPLETE_TARGETED_REFERENCE_SEMANTICS_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
