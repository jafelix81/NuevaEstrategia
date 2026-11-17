"""Conservative owner-to-transaction attribution audit for SEC ownership XML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

OWNER_REFERENCE_TAGS = {
    "reportingOwnerCik",
    "rptOwnerCik",
    "ownerCik",
    "ownerCikRef",
    "reportingOwnerRef",
}
TRANSACTION_TAGS = {"nonDerivativeTransaction", "derivativeTransaction"}


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

    owner_set = set(owner_ids)
    transaction_nodes = [
        node for node in root.iter() if local_name(node.tag) in TRANSACTION_TAGS
    ]
    assignments = []
    for index, tx in enumerate(transaction_nodes, start=1):
        refs = set()
        for child in tx.iter():
            if local_name(child.tag) not in OWNER_REFERENCE_TAGS:
                continue
            value = _text(child)
            if not value:
                value = next(
                    (
                        child.attrib[key].strip()
                        for key in ("ref", "idref", "ownerCik")
                        if child.attrib.get(key, "").strip()
                    ),
                    "",
                )
            if value:
                refs.add(canonical_owner_id(value))

        if len(refs) == 1 and next(iter(refs)) in owner_set:
            assigned = next(iter(refs))
            status = "explicit_unique_owner_reference"
        elif refs:
            assigned = None
            status = "unresolved_or_nonunique_owner_reference"
        elif len(owner_ids) == 1:
            assigned = owner_ids[0]
            status = "sole_reporting_owner"
        else:
            assigned = None
            status = "multi_owner_line_quarantined"

        assignments.append(
            {
                "transaction_index": index,
                "transaction_tag": local_name(tx.tag),
                "owner_cik": assigned,
                "status": status,
            }
        )

    ambiguous = sum(item["owner_cik"] is None for item in assignments)
    assigned = len(assignments) - ambiguous
    signatures = sum(
        1 for node in root.iter() if local_name(node.tag) == "ownerSignature"
    )

    if not owner_ids:
        disposition = "no_reporting_owner"
    elif not transaction_nodes:
        disposition = "no_transaction_lines"
    elif ambiguous:
        disposition = "quarantine_unresolved_owner_attribution"
    elif len(owner_ids) == 1:
        disposition = "single_owner_filing"
    else:
        disposition = "explicit_line_owner_mapping"

    return {
        "reporting_owner_count": len(owner_ids),
        "reporting_owner_ciks": owner_ids,
        "transaction_line_count": len(transaction_nodes),
        "uniquely_attributed_line_count": assigned,
        "ambiguous_line_count": ambiguous,
        "owner_signature_count_diagnostic_only": signatures,
        "owner_breadth_eligible": bool(transaction_nodes) and ambiguous == 0 and bool(owner_ids),
        "disposition": disposition,
        "line_assignments": assignments,
        "signature_count_used_for_attribution": False,
        "owner_order_used_for_attribution": False,
        "free_text_footnotes_auto_parsed_for_owner": False,
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
