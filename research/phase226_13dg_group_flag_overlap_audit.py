#!/usr/bin/env python3
"""Phase 226: audit Schedule 13D/G reporting-person group flags and overlap."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PHASE = 226
SOURCE_CSV_SHA256 = "be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5"
SOURCE_ZIP_SHA256 = "85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc"
EXPECTED_ROWS = 600
EXPECTED_XML_FILINGS = 102
EXPECTED_FAMILIES = {"13D": 34, "13G": 68}
OWNER_TAGS = {"13D": "reportingPersonInfo", "13G": "coverPageHeaderReportingPersonDetails"}
GROUP_TAGS = {"13D": "memberOfGroup", "13G": "memberGroup"}
AGGREGATE_TAGS = {"13D": "aggregateAmountOwned", "13G": "reportingPersonBeneficiallyOwnedAggregateNumberOfShares"}
PERCENT_TAGS = {"13D": "percentOfClass", "13G": "classPercent"}
NAMESPACE = {"13D": "http://www.sec.gov/edgar/schedule13d", "13G": "http://www.sec.gov/edgar/schedule13g"}
SIGNATURE_FIELDS = ("aggregate", "percent", "sole_voting", "shared_voting", "sole_dispositive", "shared_dispositive")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def first_text(node: ET.Element, names: set[str]) -> str:
    for element in node.iter():
        if local_name(element) in names and (element.text or "").strip():
            return (element.text or "").strip()
    return ""


def normalize_decimal(value: str) -> str:
    value = (value or "").strip().replace(",", "")
    if not value:
        return ""
    try:
        return format(Decimal(value).normalize(), "f")
    except InvalidOperation:
        return value


def extract_primary_xml(raw: bytes) -> ET.Element:
    for document in re.findall(rb"<DOCUMENT>(.*?)</DOCUMENT>", raw, re.I | re.S):
        filename = re.search(rb"<FILENAME>\s*([^\r\n<]+)", document, re.I)
        form_type = re.search(rb"<TYPE>\s*([^\r\n<]+)", document, re.I)
        if not filename or Path(filename.group(1).decode("utf-8", "replace").strip()).name.lower() != "primary_doc.xml":
            continue
        if not form_type or not re.match(rb"SCHEDULE\s+13[DG](?:/A)?$", form_type.group(1).strip(), re.I):
            continue
        xml_match = re.search(rb"<XML>(.*?)</XML>", document, re.I | re.S)
        if not xml_match:
            raise ValueError("primary_doc_xml_payload_missing")
        xml_text = xml_match.group(1).decode("utf-8-sig", "replace").strip()
        xml_text = re.sub(r"^<\?xml\s+[^?]*\?>\s*", "", xml_text, count=1, flags=re.I)
        try:
            return ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ValueError(f"primary_doc_xml_parse_error:{exc}") from exc
    raise ValueError("primary_schedule_13dg_xml_not_found")


def classify_group_flag(value: str) -> str:
    value = (value or "").strip().lower()
    if value == "a":
        return "AFFIRMED_GROUP"
    if value == "b":
        return "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION"
    if not value:
        return "UNREPORTED"
    return "INVALID_OR_UNEXPECTED"


def parse_owner(owner: ET.Element, family: str) -> dict[str, str]:
    values: dict[str, list[str]] = defaultdict(list)
    for element in owner.iter():
        value = (element.text or "").strip()
        if value:
            values[local_name(element)].append(value)

    def one(*names: str) -> str:
        for name in names:
            if values.get(name):
                return values[name][0]
        return ""

    group_raw = one(GROUP_TAGS[family])
    return {
        "group_raw": group_raw,
        "group_status": classify_group_flag(group_raw),
        "aggregate": one(AGGREGATE_TAGS[family]),
        "percent": one(PERCENT_TAGS[family]),
        "sole_voting": one("soleVotingPower"),
        "shared_voting": one("sharedVotingPower"),
        "sole_dispositive": one("soleDispositivePower"),
        "shared_dispositive": one("sharedDispositivePower"),
        "owner_cik_present": bool(one("reportingPersonCIK", "reportingPersonCik")),
    }


def signature(owner: dict[str, str]) -> tuple[str, ...]:
    return tuple(normalize_decimal(owner[field]) for field in SIGNATURE_FIELDS)


def filing_group_status(owners: list[dict[str, str]]) -> str:
    statuses = {owner["group_status"] for owner in owners}
    if "INVALID_OR_UNEXPECTED" in statuses:
        return "INVALID_OR_UNEXPECTED"
    affirmed = "AFFIRMED_GROUP" in statuses
    disclaimed = "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION" in statuses
    if affirmed and disclaimed:
        return "MIXED_AFFIRMED_AND_DISCLAIMED"
    if affirmed:
        return "AFFIRMED_PRESENT"
    if disclaimed:
        return "DISCLAIMED_OR_RELATIONSHIP_ONLY"
    return "ALL_UNREPORTED"


def summarize_family(filings: list[dict[str, Any]]) -> dict[str, Any]:
    owner_flags = Counter()
    filing_flags = Counter()
    duplicate_filings = duplicate_signature_groups = duplicate_owner_rows = 0
    duplicate_group_flags = Counter()
    mixed_duplicate_groups = all_owners_same_signature = 0
    owner_cik_present = owner_blocks = 0

    for filing in filings:
        owners = filing["owners"]
        owner_blocks += len(owners)
        owner_cik_present += sum(owner["owner_cik_present"] for owner in owners)
        owner_flags.update(owner["group_status"] for owner in owners)
        filing_flags[filing_group_status(owners)] += 1

        groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
        for owner in owners:
            sig = signature(owner)
            if any(sig):
                groups[sig].append(owner)
        repeated = [members for members in groups.values() if len(members) > 1]
        if repeated:
            duplicate_filings += 1
        if len(owners) > 1:
            all_signatures = [signature(owner) for owner in owners]
            if len(set(all_signatures)) == 1 and any(all_signatures[0]):
                all_owners_same_signature += 1
        for members in repeated:
            duplicate_signature_groups += 1
            duplicate_owner_rows += len(members)
            flags = {member["group_status"] for member in members}
            duplicate_group_flags.update(flags)
            mixed_duplicate_groups += int(len(flags) > 1)

    return {
        "filings": len(filings),
        "owner_blocks": owner_blocks,
        "owner_group_flag_status": dict(sorted(owner_flags.items())),
        "filing_group_status": dict(sorted(filing_flags.items())),
        "filings_with_any_affirmed_group": filing_flags["AFFIRMED_PRESENT"] + filing_flags["MIXED_AFFIRMED_AND_DISCLAIMED"],
        "filings_with_any_disclaimed_or_relationship_flag": filing_flags["DISCLAIMED_OR_RELATIONSHIP_ONLY"] + filing_flags["MIXED_AFFIRMED_AND_DISCLAIMED"],
        "filings_with_all_group_flags_unreported": filing_flags["ALL_UNREPORTED"],
        "reporting_person_cik_present": owner_cik_present,
        "reporting_person_cik_missing": owner_blocks - owner_cik_present,
        "filings_with_repeated_ownership_signatures": duplicate_filings,
        "repeated_signature_groups": duplicate_signature_groups,
        "owner_rows_inside_repeated_signature_groups": duplicate_owner_rows,
        "repeated_signature_groups_by_group_flag": dict(sorted(duplicate_group_flags.items())),
        "repeated_signature_groups_with_mixed_group_flags": mixed_duplicate_groups,
        "filings_where_all_owner_signatures_are_identical": all_owners_same_signature,
    }


def audit(input_dir: Path, source_zip_path: Path | None = None) -> dict[str, Any]:
    zip_sha256 = None
    zip_verified = False
    if source_zip_path is not None:
        zip_sha256 = sha256(source_zip_path.read_bytes())
        if zip_sha256 != SOURCE_ZIP_SHA256:
            raise ValueError("phase124_artifact_zip_sha256_mismatch")
        zip_verified = True

    csv_path = input_dir / "phase124_global_13dg_submission_audit.csv"
    csv_bytes = csv_path.read_bytes()
    if sha256(csv_bytes) != SOURCE_CSV_SHA256:
        raise ValueError("phase124_csv_sha256_mismatch")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_ROWS or len({row["accession"] for row in rows}) != EXPECTED_ROWS:
        raise ValueError("phase124_row_or_accession_count_mismatch")

    actual = [row for row in rows if row.get("is_index_alias", "").lower() != "true"]
    xml_rows = [row for row in actual if row.get("xml_present", "").lower() == "true"]
    if len(actual) != 599 or len(xml_rows) != EXPECTED_XML_FILINGS:
        raise ValueError("phase124_actual_or_xml_filing_count_mismatch")

    parsed: list[dict[str, Any]] = []
    for row in xml_rows:
        raw = (input_dir / row["raw_file"]).read_bytes()
        if sha256(raw) != row["raw_sha256"]:
            raise ValueError(f"raw_submission_sha256_mismatch:{row['accession']}")
        root = extract_primary_xml(raw)
        family = row["family"].strip().upper()
        if family not in OWNER_TAGS:
            raise ValueError(f"unsupported_family:{family}")
        namespace = root.tag.split("}", 1)[0].lstrip("{") if "}" in root.tag else ""
        if namespace.lower() != NAMESPACE[family].lower():
            raise ValueError(f"xml_namespace_mismatch:{row['accession']}")
        submission_type = first_text(root, {"submissionType"}).upper().replace("SCHEDULE ", "")
        if not submission_type.startswith(family):
            raise ValueError(f"xml_family_mismatch:{row['accession']}")
        owners = [parse_owner(e, family) for e in root.iter() if local_name(e) == OWNER_TAGS[family]]
        if not owners:
            raise ValueError(f"reporting_person_blocks_missing:{row['accession']}")
        parsed.append({"accession": row["accession"], "family": family, "owners": owners})

    family_results = {}
    for family in ("13D", "13G"):
        family_rows = [filing for filing in parsed if filing["family"] == family]
        if len(family_rows) != EXPECTED_FAMILIES[family]:
            raise ValueError(f"family_filing_count_mismatch:{family}")
        family_results[family] = summarize_family(family_rows)

    return {
        "phase": PHASE,
        "status": "COMPLETED_GROUP_FLAG_AND_NONADDITIVE_OWNERSHIP_SEMANTICS_AUDIT",
        "source": {
            "phase124_run_id": 42073725379,
            "phase124_artifact_id": 13436764625,
            "artifact_zip_sha256_expected": SOURCE_ZIP_SHA256,
            "artifact_zip_sha256_observed": zip_sha256,
            "artifact_zip_sha256_verified_in_this_run": zip_verified,
            "csv_sha256_verified": sha256(csv_bytes),
            "source_index_rows": len(rows),
            "actual_13dg_filings": len(actual),
            "structured_xml_filings": len(parsed),
            "raw_submission_sha256_verified": len(parsed),
            "quarters": sorted({row["quarter"] for row in xml_rows}),
        },
        "group_flag_schema": {
            "13D": "memberOfGroup",
            "13G": "memberGroup",
            "a": "AFFIRMED_GROUP",
            "b": "DISCLAIMED_OR_RELATIONSHIP_WITHOUT_AFFIRMATION",
            "missing": "UNREPORTED_NOT_NO_GROUP",
            "invalid_values": sum(owner["group_status"] == "INVALID_OR_UNEXPECTED" for filing in parsed for owner in filing["owners"]),
        },
        "by_family": family_results,
        "binding_interpretation": [
            "The group checkbox is a reporting-person-level disclosure, not a unique group identifier.",
            "A means group membership is expressly affirmed; b means membership is disclaimed or a relationship is described without affirming a group.",
            "A missing group flag is unreported/unknown, not evidence that no group exists; joint-filing rules can make the b box unnecessary.",
            "Repeated ownership tuples are not additive positions and must not be summed.",
            "Even a repeated tuple with an affirmed group flag does not identify every group member or prove a unique beneficial-owner graph.",
            "Reporting-person CIK coverage is incomplete, especially for 13G; names and filer CIKs are not stable substitutes for a permanent owner identifier.",
            "This stratified 102-XML sample is not a population prevalence estimate and covers only 2024Q4-2026Q3 structured filings.",
        ],
        "controls": {
            "forward_returns_used": False,
            "alpha_test_performed": False,
            "bootstrap_loo_performed": False,
            "final_holdout_used": False,
            "production_changed": False,
            "f80_changed": False,
            "ownership_rows_summed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-zip", type=Path, default=None)
    args = parser.parse_args()
    result = audit(args.input_dir, args.source_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
