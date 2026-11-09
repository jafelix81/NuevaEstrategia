#!/usr/bin/env python3
"""Phase 224: SEC Companyfacts / as-filed XBRL PIT shares-outstanding audit."""
from __future__ import annotations
import argparse, json, xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

SHARES_TAG = "EntityCommonStockSharesOutstanding"
PUBLIC_FLOAT_TAG = "EntityPublicFloat"
ELIGIBLE_PERIODIC_FORMS = {"10-K", "10-Q", "20-F", "40-F"}
CLASS_AXES = {"StatementClassOfStockAxis", "ClassesOfShareCapitalAxis"}


def _local_name(value: str | None) -> str:
    return value.rsplit("}", 1)[-1].split(":")[-1] if value else ""


def _as_date(value: Any) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _base_form(form: Any) -> str:
    return str(form or "").strip().upper().split("/", 1)[0]


def _unit_local(unit: Any) -> str:
    return _local_name(str(unit or "")).casefold()


def _is_shares_unit(unit: Any) -> bool:
    return _unit_local(unit) in {"shares", "share"}


def _observation_rows(companyfacts: dict) -> list[dict]:
    facts = companyfacts.get("facts", {}).get("dei", {})
    concept = facts.get(SHARES_TAG, {}) if isinstance(facts, dict) else {}
    units = concept.get("units", {}) if isinstance(concept, dict) else {}
    rows = []
    for unit, observations in (units or {}).items():
        for obs in observations or []:
            rows.append({"unit": unit, "value": obs.get("val"), "end": obs.get("end"),
                         "filed": obs.get("filed"), "accession": obs.get("accn"),
                         "form": obs.get("form"), "class_member": None})
    return rows


def select_companyfacts_shares(companyfacts: dict, event_filing_date: str) -> dict:
    event_date = _as_date(event_filing_date)
    if event_date is None:
        return {"status": "INVALID_EVENT_DATE", "value": None}
    rows = _observation_rows(companyfacts)
    if not rows:
        return {"status": "NO_ENTITY_WIDE_FACT", "value": None}
    eligible, same_day = [], 0
    rejected = {"bad_dates": 0, "future_measurement": 0, "unsupported_form": 0,
                "unit_mismatch": 0, "missing_provenance": 0, "nonpositive": 0}
    for row in rows:
        filed, end, value = _as_date(row.get("filed")), _as_date(row.get("end")), _as_decimal(row.get("value"))
        if filed is None or end is None:
            rejected["bad_dates"] += 1
            continue
        if filed == event_date:
            same_day += 1
            continue
        if filed > event_date:
            continue
        if end > event_date or end > filed:
            rejected["future_measurement"] += 1
            continue
        if _base_form(row.get("form")) not in ELIGIBLE_PERIODIC_FORMS:
            rejected["unsupported_form"] += 1
            continue
        if not _is_shares_unit(row.get("unit")):
            rejected["unit_mismatch"] += 1
            continue
        if not row.get("accession"):
            rejected["missing_provenance"] += 1
            continue
        if value is None or value <= 0:
            rejected["nonpositive"] += 1
            continue
        row = dict(row)
        row["_filed_date"], row["_end_date"], row["_value_decimal"] = filed, end, value
        eligible.append(row)
    if not eligible:
        return {"status": "SAME_DAY_ONLY" if same_day else "NO_PRIOR_ELIGIBLE_FACT",
                "value": None, "same_day_observations_excluded": same_day, "rejected": rejected}
    latest_end = max(r["_end_date"] for r in eligible)
    same_end = [r for r in eligible if r["_end_date"] == latest_end]
    latest_filed = max(r["_filed_date"] for r in same_end)
    latest_rows = [r for r in same_end if r["_filed_date"] == latest_filed]
    values = {r["_value_decimal"] for r in latest_rows}
    accessions = sorted({str(r["accession"]) for r in latest_rows})
    if len(values) != 1:
        return {"status": "AMBIGUOUS_SAME_DATE_CONFLICT", "value": None,
                "measurement_date": latest_end.isoformat(), "filed_date": latest_filed.isoformat(),
                "accessions": accessions, "conflicting_values": sorted(str(v) for v in values),
                "same_day_observations_excluded": same_day, "rejected": rejected}
    value = next(iter(values))
    return {"status": "SELECTED_ENTITY_WIDE", "value": str(value), "unit": "shares",
            "measurement_date": latest_end.isoformat(), "filed_date": latest_filed.isoformat(),
            "measurement_age_days": (event_date-latest_end).days,
            "filing_age_days": (event_date-latest_filed).days, "accessions": accessions,
            "forms": sorted({_base_form(r.get("form")) for r in latest_rows}),
            "same_day_observations_excluded": same_day,
            "class_specific_identity_proven": False, "rejected": rejected}


def extract_dei_shares_facts(xbrl_instance_xml: str) -> list[dict]:
    root = ET.fromstring(xbrl_instance_xml)
    contexts, units = {}, {}
    for node in root.iter():
        local = _local_name(node.tag)
        if local == "context":
            cid = node.attrib.get("id")
            if not cid:
                continue
            instant, members = None, []
            for child in node.iter():
                clocal = _local_name(child.tag)
                if clocal == "instant" and child.text:
                    instant = child.text.strip()
                if clocal == "explicitMember":
                    if _local_name(child.attrib.get("dimension", "")) in CLASS_AXES and child.text:
                        members.append(child.text.strip())
            contexts[cid] = {"end": instant, "class_members": sorted(set(members))}
        elif local == "unit":
            uid = node.attrib.get("id")
            if uid:
                measures = [x.text.strip() for x in node.iter() if _local_name(x.tag) == "measure" and x.text]
                if len(measures) == 1:
                    units[uid] = measures[0]
    output = []
    for node in root.iter():
        if _local_name(node.tag) != SHARES_TAG:
            continue
        cref, uref = node.attrib.get("contextRef"), node.attrib.get("unitRef")
        context = contexts.get(cref or "", {})
        value = _as_decimal((node.text or "").strip())
        members = context.get("class_members", [])
        output.append({"tag": SHARES_TAG, "value": str(value) if value is not None else None,
                       "unit": units.get(uref or ""), "end": context.get("end"),
                       "class_member": members[0] if len(members) == 1 else None,
                       "class_member_count": len(members), "class_members": members,
                       "context_ref": cref, "unit_ref": uref})
    return output


def select_class_specific_fact(records: Iterable[dict], target_member: str,
                               event_filing_date: str, fact_filed_date: str,
                               accession: str, form: str) -> dict:
    event_date, filed = _as_date(event_filing_date), _as_date(fact_filed_date)
    if event_date is None or filed is None:
        return {"status": "INVALID_EVENT_OR_FILED_DATE", "value": None}
    if filed >= event_date:
        return {"status": "SAME_DAY_OR_FUTURE_FILING", "value": None}
    if _base_form(form) not in ELIGIBLE_PERIODIC_FORMS:
        return {"status": "UNSUPPORTED_FORM", "value": None}
    if not target_member:
        return {"status": "CLASS_MEMBER_REQUIRED", "value": None}
    matches = []
    for r in records:
        if r.get("tag") != SHARES_TAG or r.get("class_member_count") != 1:
            continue
        if r.get("class_member") != target_member or not _is_shares_unit(r.get("unit")):
            continue
        end, value = _as_date(r.get("end")), _as_decimal(r.get("value"))
        if end is None or end > filed or end > event_date or value is None or value <= 0:
            continue
        matches.append((end, value))
    if not matches:
        return {"status": "CLASS_FACT_NOT_FOUND", "value": None,
                "target_member": target_member, "accession": accession}
    latest_end = max(x[0] for x in matches)
    values = {v for end, v in matches if end == latest_end}
    if len(values) != 1:
        return {"status": "AMBIGUOUS_CLASS_FACT_CONFLICT", "value": None,
                "target_member": target_member, "measurement_date": latest_end.isoformat(),
                "conflicting_values": sorted(str(v) for v in values), "accession": accession}
    value = next(iter(values))
    return {"status": "SELECTED_CLASS_SPECIFIC", "value": str(value), "unit": "shares",
            "target_member": target_member, "measurement_date": latest_end.isoformat(),
            "filed_date": filed.isoformat(), "measurement_age_days": (event_date-latest_end).days,
            "filing_age_days": (event_date-filed).days, "accession": accession,
            "form": _base_form(form), "class_specific_identity_proven": True}


def classify_dei_measure(tag: str, unit: str) -> str:
    if tag == PUBLIC_FLOAT_TAG:
        return "PUBLIC_FLOAT_MARKET_VALUE_NOT_SHARES" if _unit_local(unit) in {"usd", "iso4217:usd"} else "PUBLIC_FLOAT_UNIT_REVIEW"
    if tag == SHARES_TAG:
        return "SHARES_OUTSTANDING" if _is_shares_unit(unit) else "SHARES_UNIT_MISMATCH"
    return "UNSUPPORTED_DEI_CONCEPT"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--companyfacts", type=Path, required=True)
    parser.add_argument("--event-filing-date", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = select_companyfacts_shares(json.loads(args.companyfacts.read_text(encoding="utf-8")),
                                        args.event_filing_date)
    result.update({"phase": 224, "source_contract": "SEC_COMPANYFACTS_ENTITY_WIDE_ONLY"})
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
