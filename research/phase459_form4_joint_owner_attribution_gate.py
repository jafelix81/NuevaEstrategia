"""Fail-closed Form 4 owner attribution audit.

A transaction-to-owner foreign key is not admitted unless an exact element is
verified against the applicable SEC Ownership XSD. The current v5.5 ZIP was
not available for inspection during Phase 460, so multi-owner lines remain
quarantined. A sole reporting owner is attributed only at filing grain.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

TRANSACTION_TAGS = {"nonDerivativeTransaction", "derivativeTransaction"}
UNVERIFIED_OWNER_REFERENCE_TAGS = {
    "reportingOwnerCik",
    "rptOwnerCik",
    "ownerCik",
    "ownerCikRef",
    "reportingOwnerRef",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def canonical_owner_id(value: str | None) -> str:
    raw = (value or "").strip()
    if raw.isdigit():
        return raw.zfill(10)
    return raw


def _text(node: ET.Element) -> str:
    return (node.text or "").strip()


def audit_ownership_xml(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    schema_version = next(
        (_text(node) for node in root if local_name(node.tag) == "schemaVersion"),
        None,
    )

    owner_ids: list[str] = []
    for node in root.iter():
        if local_name(node.tag) != "reportingOwner":
            continue
        cik_values = [
            canonical_owner_id(_text(child))
            for child in node.iter()
            if local_name(child.tag) == "rptOwnerCik" and _text(child)
        ]
        if len(cik_values) != 1:
            raise ValueError("each reportingOwner must contain exactly one nonblank rptOwnerCik")
        owner_ids.append(cik_values[0])

    if len(owner_ids) != len(set(owner_ids)):
        raise ValueError("duplicate reporting-owner CIK")

    transaction_nodes = [
        node for node in root.iter() if local_name(node.tag) in TRANSACTION_TAGS
    ]
    assignments = []
    unverified_tags_seen: set[str] = set()
    unverified_reference_count = 0

    for index, tx in enumerate(transaction_nodes, start=1):
        tags = sorted({
            local_name(child.tag)
            for child in tx.iter()
            if local_name(child.tag) in UNVERIFIED_OWNER_REFERENCE_TAGS
        })
        unverified_tags_seen.update(tags)
        unverified_reference_count += len(tags)

        if len(owner_ids) == 1:
            assigned = owner_ids[0]
            status = (
                "sole_reporting_owner_filing_grain"
                if not tags
                else "sole_reporting_owner_filing_grain_unverified_token_ignored"
            )
        elif len(owner_ids) > 1:
            assigned = None
            status = "multi_owner_line_quarantined"
        else:
            assigned = None
            status = "no_reporting_owner"

        assignments.append({
            "transaction_index": index,
            "transaction_tag": local_name(tx.tag),
            "owner_cik": assigned,
            "status": status,
            "unverified_owner_reference_tags_ignored": tags,
        })

    ambiguous = sum(item["owner_cik"] is None for item in assignments)
    signatures = sum(
        1 for node in root.iter() if local_name(node.tag) == "ownerSignature"
    )
    if not owner_ids:
        disposition = "no_reporting_owner"
    elif not transaction_nodes:
        disposition = "no_transaction_lines"
    elif len(owner_ids) == 1:
        disposition = "single_owner_filing_grain_only"
    else:
        disposition = "quarantine_all_multi_owner_transaction_lines"

    return {
        "schema_version": schema_version,
        "reporting_owner_count": len(owner_ids),
        "reporting_owner_ciks": owner_ids,
        "transaction_line_count": len(transaction_nodes),
        "uniquely_attributed_line_count": len(assignments) - ambiguous,
        "ambiguous_line_count": ambiguous,
        "owner_signature_count_diagnostic_only": signatures,
        "owner_breadth_eligible": bool(transaction_nodes) and len(owner_ids) == 1,
        "explicit_line_owner_mapping_count": 0,
        "schema_approved_line_owner_reference_tags": [],
        "schema_reference_gate": "NOT_VERIFIED_FAIL_CLOSED",
        "unverified_owner_reference_count": unverified_reference_count,
        "unverified_owner_reference_tags_seen": sorted(unverified_tags_seen),
        "disposition": disposition,
        "line_assignments": assignments,
        "signature_count_used_for_attribution": False,
        "owner_order_used_for_attribution": False,
        "free_text_footnotes_auto_parsed_for_owner": False,
        "multi_owner_rows_admitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_ownership_xml(args.xml.read_text(encoding="utf-8"))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
