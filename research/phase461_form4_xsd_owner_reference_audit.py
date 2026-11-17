"""Audit SEC Ownership Form 4/4A XSD structure for transaction-owner links."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

XS = "{http://www.w3.org/2001/XMLSchema}"
OWNER_LINK_NAMES = {
    "reportingownercik",
    "rptownercik",
    "ownercik",
    "reportingownerref",
    "ownerref",
    "reportingownerid",
    "ownerid",
}


def _parse(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    if root.tag != XS + "schema":
        raise ValueError(f"{path.name}: root is not xs:schema")
    return root


def _named_complex_types(roots: list[ET.Element]) -> dict[str, ET.Element]:
    result: dict[str, ET.Element] = {}
    for root in roots:
        for node in root.findall(XS + "complexType"):
            name = node.get("name")
            if name:
                result[name] = node
    return result


def _direct_sequence_fields(node: ET.Element) -> list[str]:
    sequence = node.find(XS + "sequence")
    if sequence is None:
        return []
    return [item.get("name", "") for item in sequence.findall(XS + "element")]


def _collect_type_elements(
    type_name: str,
    type_map: dict[str, ET.Element],
    visited: set[str] | None = None,
) -> set[str]:
    visited = set() if visited is None else visited
    if type_name in visited or type_name not in type_map:
        return set()
    visited.add(type_name)
    node = type_map[type_name]
    names: set[str] = set()
    for element in node.iter(XS + "element"):
        name = element.get("name")
        if name:
            names.add(name)
        child_type = element.get("type")
        if child_type:
            names.update(_collect_type_elements(child_type, type_map, visited))
    return names


def _root_sequence(root: ET.Element) -> list[dict[str, str]]:
    ownership = next(
        (item for item in root.findall(XS + "element") if item.get("name") == "ownershipDocument"),
        None,
    )
    if ownership is None:
        raise ValueError("ownershipDocument root element not found")
    complex_type = ownership.find(XS + "complexType")
    if complex_type is None:
        raise ValueError("ownershipDocument has no anonymous complexType")
    sequence = complex_type.find(XS + "sequence")
    if sequence is None:
        raise ValueError("ownershipDocument has no xs:sequence")
    return [
        {
            "name": item.get("name", ""),
            "min_occurs": item.get("minOccurs", "1"),
            "max_occurs": item.get("maxOccurs", "1"),
        }
        for item in sequence.findall(XS + "element")
    ]


def _table_limit(type_map: dict[str, ET.Element], name: str) -> str | None:
    node = type_map.get(name)
    if node is None:
        return None
    choice = node.find(XS + "choice")
    return choice.get("maxOccurs") if choice is not None else None


def audit_schema_dir(schema_dir: Path) -> dict:
    names = [
        "ownership4Document.xsd.xml",
        "ownership4ADocument.xsd.xml",
        "ownershipDocumentCommon.xsd.xml",
    ]
    paths = [schema_dir / name for name in names]
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        return {"status": "NOT_VERIFIED_FAIL_CLOSED", "errors": [f"missing: {x}" for x in missing]}

    try:
        form4, form4a, common = [_parse(path) for path in paths]
    except Exception as exc:
        return {"status": "NOT_VERIFIED_FAIL_CLOSED", "errors": [str(exc)]}

    type_map = _named_complex_types([form4, form4a, common])
    required_types = [
        "NONDERIVATIVE_TRANSACTION",
        "DERIVATIVE_TRANSACTION",
        "NONDERIVATIVE_TABLE",
        "DERIVATIVE_TABLE",
    ]
    missing_types = [name for name in required_types if name not in type_map]
    if missing_types:
        return {
            "status": "NOT_VERIFIED_FAIL_CLOSED",
            "errors": [f"missing complex types: {', '.join(missing_types)}"],
        }

    form4_types = _named_complex_types([form4, common])
    form4a_types = _named_complex_types([form4a, common])
    nd_fields = _direct_sequence_fields(form4_types["NONDERIVATIVE_TRANSACTION"])
    d_fields = _direct_sequence_fields(form4_types["DERIVATIVE_TRANSACTION"])
    nd_fields_4a = _direct_sequence_fields(form4a_types["NONDERIVATIVE_TRANSACTION"])
    d_fields_4a = _direct_sequence_fields(form4a_types["DERIVATIVE_TRANSACTION"])

    all_schema_nodes = [node for root in [form4, form4a, common] for node in root.iter()]
    wildcard_counts = {
        "any": sum(node.tag == XS + "any" for node in all_schema_nodes),
        "anyAttribute": sum(node.tag == XS + "anyAttribute" for node in all_schema_nodes),
    }
    identity_counts = {
        "key": sum(node.tag == XS + "key" for node in all_schema_nodes),
        "keyref": sum(node.tag == XS + "keyref" for node in all_schema_nodes),
        "unique": sum(node.tag == XS + "unique" for node in all_schema_nodes),
    }

    nested_names = (
        _collect_type_elements("NONDERIVATIVE_TRANSACTION", form4_types)
        | _collect_type_elements("DERIVATIVE_TRANSACTION", form4_types)
    )
    owner_refs = sorted(name for name in nested_names if name.lower() in OWNER_LINK_NAMES)

    root_fields = _root_sequence(form4)
    root_by_name = {item["name"]: item for item in root_fields}
    reporting_owner_max = root_by_name.get("reportingOwner", {}).get("max_occurs")
    signature_max = root_by_name.get("ownerSignature", {}).get("max_occurs")
    nd_limit = _table_limit(form4_types, "NONDERIVATIVE_TABLE")
    d_limit = _table_limit(form4_types, "DERIVATIVE_TABLE")

    errors: list[str] = []
    if nd_fields != nd_fields_4a or d_fields != d_fields_4a:
        errors.append("Form 4 and Form 4/A transaction structures differ")
    if reporting_owner_max is None:
        errors.append("reportingOwner root element missing")
    if nd_limit is None or d_limit is None:
        errors.append("one or both transaction-table limits are missing")
    if any(wildcard_counts.values()):
        errors.append("schema contains wildcard elements/attributes")
    if any(identity_counts.values()):
        errors.append("schema contains identity constraints requiring manual review")

    if errors:
        status = "NOT_VERIFIED_FAIL_CLOSED"
    elif owner_refs:
        status = "OWNER_REFERENCE_PRESENT_REQUIRES_MANUAL_REVIEW"
    else:
        status = "NO_SCHEMA_DEFINED_TRANSACTION_TO_OWNER_LINK"

    return {
        "status": status,
        "errors": errors,
        "form4_nonderivative_transaction_elements": nd_fields,
        "form4_derivative_transaction_elements": d_fields,
        "form4a_transaction_structures_match": nd_fields == nd_fields_4a and d_fields == d_fields_4a,
        "transaction_nested_element_names": sorted(nested_names),
        "transaction_owner_reference_elements": owner_refs,
        "root_sequence": root_fields,
        "reporting_owner_max_occurs": reporting_owner_max,
        "owner_signature_max_occurs": signature_max,
        "nonderivative_table_max_rows": nd_limit,
        "derivative_table_max_rows": d_limit,
        "wildcard_counts": wildcard_counts,
        "identity_constraint_counts": identity_counts,
        "multi_owner_line_attribution_allowed": False,
        "note": "Even a newly found owner-reference element requires semantic and official-archive verification before admission.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema-dir", required=True, type=Path)
    args = parser.parse_args()
    result = audit_schema_dir(args.schema_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "NO_SCHEMA_DEFINED_TRANSACTION_TO_OWNER_LINK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
