#!/usr/bin/env python3
"""Phase 161: audit reuse and issuer/security scope of SEC 13D/G previous-accession references.

The fixture is a targeted, non-random set of public SEC XML filings. The audit does
not assume that a previousAccessionNumber is an issuer-level parent until the
referenced document is inspected and issuer/security continuity is established.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

PREVIOUS_ACCESSION = "0001445546-21-002430"

SAMPLE_ROWS = [
    {
        "child_accession": "0001445546-25-002780",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0001667919",
        "issuer_name": "First Trust Exchange-Traded Fund VIII",
        "security_class": "FT Vest U.S. Small Cap Moderate Buffer ETF - November",
        "cusip": "33740F342",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554625002780/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-25-002771",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0000904112",
        "issuer_name": "Morgan Stanley Emerging Markets Domestic Debt Fund, Inc.",
        "security_class": "Common",
        "cusip": "617477104",
        "source_url": "https://www.sec.gov/Archives/edgar/data/904112/000144554625002771/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-25-002779",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0001667919",
        "issuer_name": "First Trust Exchange-Traded Fund VIII",
        "security_class": "FT Vest U.S. Small Cap Moderate Buffer ETF - May",
        "cusip": "33740F466",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554625002779/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-25-004973",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0001667919",
        "issuer_name": "First Trust Exchange-Traded Fund VIII",
        "security_class": "FT Vest U.S. Equity Deep Buffer ETF - September",
        "cusip": "33740F680",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1667919/000144554625004973/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-26-007700",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0001667919",
        "issuer_name": "First Trust Exchange-Traded Fund VIII",
        "security_class": "FT Vest U.S. Equity Moderate Buffer ETF - November",
        "cusip": "33740U687",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554626007700/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-26-008202",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0000779336",
        "issuer_name": "abrdn Australia Equity Fund, Inc.",
        "security_class": "Common",
        "cusip": "003011111",
        "source_url": "https://www.sec.gov/Archives/edgar/data/779336/000144554626008202/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-26-008249",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0000908315",
        "issuer_name": "Winmark Corporation",
        "security_class": "Common",
        "cusip": "974250102",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554626008249/primary_doc.xml",
    },
    {
        "child_accession": "0001445546-26-008161",
        "previous_accession": PREVIOUS_ACCESSION,
        "form": "SCHEDULE 13G/A",
        "issuer_cik": "0000855887",
        "issuer_name": "BNY Mellon Strategic Municipal Bond Fund, Inc.",
        "security_class": "Common",
        "cusip": "09662E109",
        "source_url": "https://www.sec.gov/Archives/edgar/data/1184765/000144554626008161/primary_doc.xml",
    },
]


def normalize_accession(value: str) -> str | None:
    match = re.fullmatch(r"\s*(\d{1,10})-(\d{2})-(\d{1,6})\s*", str(value or ""))
    if not match:
        return None
    return f"{int(match.group(1)):010d}-{match.group(2)}-{int(match.group(3)):06d}"


def _parent_status(rows: list[dict], parent_document: dict | None) -> tuple[str, bool]:
    if parent_document is None:
        issuer_count = len({r["issuer_cik"] for r in rows})
        cusip_count = len({r["cusip"] for r in rows if r["cusip"]})
        if issuer_count > 1:
            return "CROSS_ISSUER_REFERENCE_REUSE_QUARANTINE", False
        if cusip_count > 1:
            return "MULTI_SECURITY_REFERENCE_REUSE_QUARANTINE", False
        return "UNVERIFIED_PREVIOUS_ACCESSION_REFERENCE", False

    parent_issuer = str(parent_document.get("issuer_cik", "")).zfill(10)
    parent_cusips = {str(x).strip() for x in parent_document.get("cusips", []) if str(x).strip()}
    child_issuers = {r["issuer_cik"] for r in rows}
    child_cusips = {r["cusip"] for r in rows if r["cusip"]}

    if len(child_issuers) != 1 or parent_issuer not in child_issuers:
        return "PARENT_DOCUMENT_ISSUER_MISMATCH", False
    if not parent_cusips or not child_cusips.intersection(parent_cusips):
        return "PARENT_DOCUMENT_SECURITY_MISMATCH_OR_CUSIP_TRANSITION", False
    # A same-issuer/CUSIP match is only a continuity candidate. Corporate actions,
    # share-class changes and historical CUSIP effectiveness still need adjudication.
    return "PARENT_DOCUMENT_ISSUER_CUSIP_CONTINUITY_CANDIDATE", False


def audit(rows: list[dict], parent_documents: dict | None = None) -> tuple[list[dict], dict]:
    parent_documents = parent_documents or {}
    groups: dict[str, list[dict]] = defaultdict(list)
    seen_children: set[str] = set()
    normalized_rows = []
    invalid_rows = []

    for raw in rows:
        child = normalize_accession(raw.get("child_accession", ""))
        previous = normalize_accession(raw.get("previous_accession", ""))
        issuer = str(raw.get("issuer_cik", "")).strip().zfill(10)
        cusip = str(raw.get("cusip", "")).strip()
        if not child or not issuer.isdigit() or not cusip:
            invalid_rows.append(raw)
            continue
        if child in seen_children:
            invalid_rows.append(raw)
            continue
        seen_children.add(child)
        row = dict(raw)
        row["child_accession"] = child
        row["previous_accession"] = previous or ""
        row["issuer_cik"] = issuer
        row["cusip"] = cusip
        normalized_rows.append(row)
        if previous:
            groups[previous].append(row)

    group_rows = []
    for previous, members in sorted(groups.items()):
        issuer_ciks = sorted({r["issuer_cik"] for r in members})
        cusips = sorted({r["cusip"] for r in members})
        parent_document = parent_documents.get(previous)
        status, verified = _parent_status(members, parent_document)
        group_rows.append({
            "previous_accession": previous,
            "child_count": len(members),
            "unique_child_accessions": len({r["child_accession"] for r in members}),
            "issuer_ciks": issuer_ciks,
            "unique_issuer_cik_count": len(issuer_ciks),
            "cusips": cusips,
            "unique_cusip_count": len(cusips),
            "status": status,
            "parent_document_inspected": parent_document is not None,
            "issuer_security_parent_verified": verified,
            "child_accessions": sorted(r["child_accession"] for r in members),
        })

    total_children = sum(g["child_count"] for g in group_rows)
    cross_issuer = sum(g["unique_issuer_cik_count"] > 1 for g in group_rows)
    multi_security = sum(g["unique_cusip_count"] > 1 for g in group_rows)
    summary = {
        "phase": 161,
        "status": "CROSS_ISSUER_REFERENCE_REUSE_DETECTED" if cross_issuer else "NO_CROSS_ISSUER_REUSE_IN_TARGETED_SAMPLE",
        "sample_design": "TARGETED_NON_RANDOM_PUBLIC_SEC_XML_CONTROL_SET",
        "input_rows": len(rows),
        "valid_unique_child_rows": len(normalized_rows),
        "invalid_or_duplicate_child_rows": len(invalid_rows),
        "children_with_previous_accession": total_children,
        "unique_previous_accessions": len(group_rows),
        "max_children_per_previous_accession": max((g["child_count"] for g in group_rows), default=0),
        "cross_issuer_reference_groups": cross_issuer,
        "multi_cusip_reference_groups": multi_security,
        "distinct_issuer_ciks_across_linked_children": sorted({r["issuer_cik"] for r in normalized_rows if r["previous_accession"]}),
        "distinct_issuer_cik_count": len({r["issuer_cik"] for r in normalized_rows if r["previous_accession"]}),
        "distinct_cusip_count": len({r["cusip"] for r in normalized_rows if r["previous_accession"]}),
        "parent_documents_inspected": sum(g["parent_document_inspected"] for g in group_rows),
        "issuer_security_parent_verified": sum(g["issuer_security_parent_verified"] for g in group_rows),
        "groups": group_rows,
        "decision": (
            "previousAccessionNumber is an accession reference, not a verified issuer/security parent by itself. "
            "A single value is reused by sampled amendments covering multiple issuer CIKs and CUSIPs. "
            "Keep the reference for provenance, quarantine issuer/security continuity, and inspect the referenced "
            "submission plus effective-dated security identity before reconstructing an amendment chain."
        ),
        "forward_returns_used": False,
        "final_holdout_used": False,
        "production_changed": False,
    }
    return group_rows, summary


def write_outputs(groups: list[dict], summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase161_13dg_previous_accession_semantics_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    csv_path = output_dir / "phase161_13dg_previous_accession_semantics_groups.csv"
    fields = [
        "previous_accession", "child_count", "unique_child_accessions",
        "unique_issuer_cik_count", "issuer_ciks", "unique_cusip_count",
        "cusips", "status", "parent_document_inspected",
        "issuer_security_parent_verified", "child_accessions",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for group in groups:
            writer.writerow({**group,
                "issuer_ciks": "|".join(group["issuer_ciks"]),
                "cusips": "|".join(group["cusips"]),
                "child_accessions": "|".join(group["child_accessions"]),
            })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    groups, summary = audit(SAMPLE_ROWS)
    write_outputs(groups, summary, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "CROSS_ISSUER_REFERENCE_REUSE_DETECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
