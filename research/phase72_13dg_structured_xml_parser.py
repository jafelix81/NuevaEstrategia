"""Deterministic parser for SEC Schedule 13D/13G structured XML.

The SEC uses different element names for 13D and 13G. This module deliberately
keeps reporting persons separate and never substitutes the accession-prefix or
submission filer CIK for a missing reporting-person CIK.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any


PARSER_VERSION = "phase72-v1"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _children(node: ET.Element | None, name: str) -> list[ET.Element]:
    if node is None:
        return []
    return [child for child in list(node) if _local(child.tag) == name]


def _child(node: ET.Element | None, name: str) -> ET.Element | None:
    found = _children(node, name)
    return found[0] if found else None


def _text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def _value(node: ET.Element | None, *path: str) -> str:
    cur = node
    for part in path:
        cur = _child(cur, part)
        if cur is None:
            return ""
    return _text(cur)


def _values(node: ET.Element | None, name: str) -> list[str]:
    return [v for v in (_text(x) for x in _children(node, name)) if v]


def _cik(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""
    return digits.zfill(10) if len(digits) <= 10 else digits


def _person_identity(cik: str, no_cik_flag: str) -> dict[str, str]:
    normalized = _cik(cik)
    flag = (no_cik_flag or "").strip().upper()
    if normalized:
        status = "cik_present"
    elif flag == "Y":
        status = "declared_no_cik"
    elif flag == "N":
        status = "cik_expected_but_missing"
    else:
        status = "cik_unreported"
    return {
        "person_cik": normalized,
        "person_no_cik_flag": flag,
        "person_cik_status": status,
    }


def _parse_13d(form_data: ET.Element, header: ET.Element) -> dict[str, Any]:
    cover = _child(form_data, "coverPageHeader")
    issuer = _child(cover, "issuerInfo")
    persons_parent = _child(form_data, "reportingPersons")
    people = []
    for info in _children(persons_parent, "reportingPersonInfo"):
        identity = _person_identity(
            _value(info, "reportingPersonCIK"),
            _value(info, "reportingPersonNoCIK"),
        )
        people.append({
            **identity,
            "name": _value(info, "reportingPersonName"),
            "member_of_group": _value(info, "memberOfGroup"),
            "citizenship_or_organization": _value(info, "citizenshipOrOrganization"),
            "fund_types": _values(info, "fundType"),
            "type_codes": _values(info, "typeOfReportingPerson"),
            "sole_voting_power": _value(info, "soleVotingPower"),
            "shared_voting_power": _value(info, "sharedVotingPower"),
            "sole_dispositive_power": _value(info, "soleDispositivePower"),
            "shared_dispositive_power": _value(info, "sharedDispositivePower"),
            "aggregate_amount_owned": _value(info, "aggregateAmountOwned"),
            "percent_of_class": _value(info, "percentOfClass"),
            "comments": _value(info, "commentContent"),
        })
    items = _child(form_data, "items1To7")
    item2 = _child(items, "item2")
    item4 = _child(items, "item4")
    return {
        "issuer_cik": _cik(_value(issuer, "issuerCIK")),
        "issuer_name": _value(issuer, "issuerName"),
        "cusips": [_value(issuer, "issuerCUSIP")] if _value(issuer, "issuerCUSIP") else [],
        "event_date": _value(cover, "dateOfEvent"),
        "amendment_number": _value(cover, "amendmentNo"),
        "previous_accession_number": _value(header, "previousAccessionNumber"),
        "reporting_persons": people,
        "filing_person_name_narrative": _value(item2, "filingPersonName"),
        "purpose_text": _value(item4, "transactionPurpose"),
        "rule_designations": [],
        "group_members_narrative": "",
    }


def _parse_13g(form_data: ET.Element, header: ET.Element) -> dict[str, Any]:
    cover = _child(form_data, "coverPageHeader")
    issuer = _child(cover, "issuerInfo")
    cusips = []
    direct_cusip = _value(issuer, "issuerCusip")
    if direct_cusip:
        cusips.append(direct_cusip)
    cusips.extend(_values(_child(issuer, "issuerCusips"), "issuerCusipNumber"))
    people = []
    for info in _children(form_data, "coverPageHeaderReportingPersonDetails"):
        identity = _person_identity(
            _value(info, "reportingCik"),
            _value(info, "reportingCikNotPresentInEdgarFlag"),
        )
        shares = _child(info, "reportingPersonBeneficiallyOwnedNumberOfShares")
        people.append({
            **identity,
            "name": _value(info, "reportingPersonName"),
            "member_of_group": _value(info, "memberGroup"),
            "citizenship_or_organization": _value(info, "citizenshipOrOrganization"),
            "fund_types": [],
            "type_codes": _values(info, "typeOfReportingPerson"),
            "sole_voting_power": _value(shares, "soleVotingPower"),
            "shared_voting_power": _value(shares, "sharedVotingPower"),
            "sole_dispositive_power": _value(shares, "soleDispositivePower"),
            "shared_dispositive_power": _value(shares, "sharedDispositivePower"),
            "aggregate_amount_owned": _value(
                info, "reportingPersonBeneficiallyOwnedAggregateNumberOfShares"
            ),
            "percent_of_class": _value(info, "classPercent"),
            "comments": _value(info, "comments"),
        })
    rules_parent = _child(cover, "designateRulesPursuantThisScheduleFiled")
    rules = _values(rules_parent, "designateRulePursuantThisScheduleFiled")
    items = _child(form_data, "items")
    item2 = _child(items, "item2")
    item8 = _child(items, "item8")
    return {
        "issuer_cik": _cik(_value(issuer, "issuerCik")),
        "issuer_name": _value(issuer, "issuerName"),
        "cusips": list(dict.fromkeys(cusips)),
        "event_date": _value(cover, "eventDateRequiresFilingThisStatement"),
        "amendment_number": _value(cover, "amendmentNo"),
        "previous_accession_number": _value(header, "previousAccessionNumber"),
        "reporting_persons": people,
        "filing_person_name_narrative": _value(item2, "filingPersonName"),
        "purpose_text": "",
        "rule_designations": rules,
        "group_members_narrative": _value(
            item8, "identificationAndClassificationOfGroupMembers"
        ),
    }


def parse_schedule13_xml(raw: bytes | str) -> dict[str, Any]:
    """Parse a Schedule 13D/13G primary_doc.xml into filing/person records.

    filing_date is intentionally not inferred from the XML. Callers must attach
    the SEC submissions filingDate as the conservative KnowledgeDate.
    """
    data = raw.encode("utf-8") if isinstance(raw, str) else raw
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"not valid Schedule 13D/13G XML: {exc}") from exc

    root_name = _local(root.tag).lower()
    header = _child(root, "headerData")
    form_data = _child(root, "formData")
    if form_data is None:
        raise ValueError("missing formData")
    submission_type = _value(header, "submissionType").upper()
    if "13D" in submission_type or "schedule13d" in root_name:
        family = "13D"
        parsed = _parse_13d(form_data, header)
    elif "13G" in submission_type or "schedule13g" in root_name:
        family = "13G"
        parsed = _parse_13g(form_data, header)
    else:
        raise ValueError(f"unsupported Schedule 13D/13G submissionType: {submission_type!r}")

    is_amendment = submission_type.endswith("/A")
    previous = parsed["previous_accession_number"].strip()
    if is_amendment and previous:
        lineage_status = "direct_predecessor_present"
    elif is_amendment:
        lineage_status = "amendment_missing_predecessor"
    elif previous:
        lineage_status = "unexpected_predecessor_on_original"
    else:
        lineage_status = "original_no_predecessor"

    filer_info = _child(header, "filerInfo")
    filer_cik = _cik(
        _value(filer_info, "cik")
        or _value(filer_info, "filer", "filerCredentials", "cik")
    )
    return {
        "parser_version": PARSER_VERSION,
        "form_family": family,
        "submission_type": submission_type,
        "is_amendment": is_amendment,
        "filer_cik_xml": filer_cik,
        "previous_accession_number": previous,
        "lineage_status": lineage_status,
        "issuer_cik": parsed["issuer_cik"],
        "issuer_name": parsed["issuer_name"],
        "cusips": parsed["cusips"],
        "event_date": parsed["event_date"],
        "amendment_number": parsed["amendment_number"],
        "reporting_person_count": len(parsed["reporting_persons"]),
        "reporting_persons": parsed["reporting_persons"],
        "filing_person_name_narrative": parsed["filing_person_name_narrative"],
        "purpose_text": parsed["purpose_text"],
        "rule_designations": parsed["rule_designations"],
        "group_members_narrative": parsed["group_members_narrative"],
        "knowledge_date": "",
        "knowledge_date_source": "SEC submissions filingDate required; never event_date",
    }
