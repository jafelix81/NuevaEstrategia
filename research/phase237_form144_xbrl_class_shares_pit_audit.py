"""Phase 237: fail-closed SEC XBRL class-specific shares-outstanding audit.

This module is an offline measurement contract. It does not fetch SEC data,
construct a security master, estimate float/ADV, or authorize alpha testing.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Iterable

SHARES_CONCEPT = "dei:EntityCommonStockSharesOutstanding"
PUBLIC_FLOAT_CONCEPT = "dei:EntityPublicFloat"
ALLOWED_CLASS_AXES = {
    "us-gaap:StatementClassOfStockAxis",
    "us-gaap:ClassesOfShareCapitalAxis",
}


def _d(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def _aware_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def companyfacts_can_supply_fact(fact: dict[str, Any]) -> bool:
    """Company Facts scope permits entity-wide facts, not dimensioned class facts."""
    return fact.get("concept") == SHARES_CONCEPT and not fact.get("dimensions")


def validate_share_fact(fact: dict[str, Any]) -> tuple[bool, str]:
    if fact.get("concept") != SHARES_CONCEPT:
        return False, "WRONG_CONCEPT"
    if str(fact.get("unit", "")).lower() not in {"shares", "xbrli:shares"}:
        return False, "WRONG_UNIT"
    if fact.get("start") not in (None, ""):
        return False, "NOT_INSTANT_CONTEXT"
    end = _d(fact.get("end"))
    filed = _d(fact.get("filed"))
    if end is None or filed is None:
        return False, "MISSING_OR_INVALID_DATE"
    if end > filed:
        return False, "FACT_DATE_AFTER_FILING"
    try:
        value = float(fact.get("value"))
    except (TypeError, ValueError):
        return False, "INVALID_VALUE"
    if value < 0 or not value.is_integer():
        return False, "INVALID_SHARE_COUNT"
    if not fact.get("accession"):
        return False, "MISSING_ACCESSION"
    dims = fact.get("dimensions") or []
    if dims:
        if len(dims) != 1:
            return False, "MULTIPLE_DIMENSIONS_UNSUPPORTED"
        if dims[0].get("axis") not in ALLOWED_CLASS_AXES:
            return False, "UNSUPPORTED_DIMENSION_AXIS"
        if not dims[0].get("member"):
            return False, "MISSING_CLASS_MEMBER"
    return True, "VALID"


def _resolve_accession_group(
    rows: list[dict[str, Any]],
    target_member: str | None,
    known_common_class_count: int | None,
) -> dict[str, Any]:
    end_dates = {_d(r.get("end")) for r in rows}
    if len(end_dates) != 1:
        return {"status": "MIXED_CLASS_FACT_DATES", "shares": None}
    dimensions = [r.get("dimensions") or [] for r in rows]
    dimensioned = [bool(x) for x in dimensions]
    if any(dimensioned) and not all(dimensioned):
        return {"status": "MIXED_DIMENSIONAL_AND_ENTITY_WIDE", "shares": None}
    if not any(dimensioned):
        values = {int(float(r["value"])) for r in rows}
        if len(values) != 1:
            return {"status": "CONFLICTING_ENTITY_WIDE_FACTS", "shares": None}
        if known_common_class_count != 1:
            return {"status": "ENTITY_WIDE_CLASS_COUNT_NOT_PROVEN_ONE", "shares": None}
        return {"status": "ENTITY_WIDE_SINGLE_CLASS", "shares": values.pop()}

    axes = {r["dimensions"][0]["axis"] for r in rows}
    if len(axes) != 1:
        return {"status": "MULTIPLE_CLASS_AXES", "shares": None}
    members = {r["dimensions"][0]["member"] for r in rows}
    if len(members) < 2:
        return {"status": "INCOMPLETE_CLASS_DIMENSION_SET", "shares": None}
    if known_common_class_count is not None and len(members) != known_common_class_count:
        return {"status": "CLASS_COUNT_MISMATCH", "shares": None}
    if target_member is None:
        return {"status": "EXACT_CLASS_MEMBER_REQUIRED", "shares": None}
    target_rows = [r for r in rows if r["dimensions"][0]["member"] == target_member]
    if not target_rows:
        return {"status": "TARGET_CLASS_MEMBER_NOT_FOUND", "shares": None}
    values = {int(float(r["value"])) for r in target_rows}
    if len(values) != 1:
        return {"status": "CONFLICTING_TARGET_CLASS_FACTS", "shares": None}
    return {"status": "CLASS_DIMENSIONED_EXACT_MEMBER", "shares": values.pop()}


def resolve_asof_shares(
    facts: Iterable[dict[str, Any]],
    event_filed_date: str,
    target_member: str | None,
    known_common_class_count: int | None,
) -> dict[str, Any]:
    """Resolve the latest as-filed class share count available by a Form 144 date.

    This returns total shares outstanding for an exact class only. It is not
    public float, freely tradable shares, ADV, or a supply-pressure feature.
    """
    event_date = _d(event_filed_date)
    if event_date is None:
        return {"status": "INVALID_EVENT_DATE", "shares": None}

    all_facts = list(facts)
    eligible: list[dict[str, Any]] = []
    rejected: dict[str, int] = defaultdict(int)
    invalid_asof_dates: list[date] = []
    for fact in all_facts:
        if fact.get("concept") != SHARES_CONCEPT:
            continue
        filed = _d(fact.get("filed"))
        if filed is None:
            rejected["UNDATED_SHARE_FACT"] += 1
            return {"status": "UNDATED_SOURCE_FACT_PRESENT", "shares": None,
                    "rejected": dict(rejected)}
        if filed > event_date:
            rejected["FILED_AFTER_EVENT"] += 1
            continue
        ok, reason = validate_share_fact(fact)
        if not ok:
            rejected[reason] += 1
            invalid_asof_dates.append(filed)
            continue
        eligible.append(fact)
    if not eligible:
        return {"status": "NO_ELIGIBLE_FACT", "shares": None, "rejected": dict(rejected)}

    by_accession: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in eligible:
        by_accession[str(fact["accession"])].append(fact)

    resolved: list[dict[str, Any]] = []
    for accession, rows in by_accession.items():
        filing_dates = {_d(r["filed"]) for r in rows}
        acceptance_values = {r.get("acceptance_datetime") for r in rows if r.get("acceptance_datetime")}
        if len(filing_dates) != 1:
            continue
        group = _resolve_accession_group(rows, target_member, known_common_class_count)
        resolved.append({
            **group,
            "accession": accession,
            "filed": next(iter(filing_dates)).isoformat(),
            "end": max(_d(r["end"]) for r in rows).isoformat(),
            "acceptance_datetime": next(iter(acceptance_values)) if len(acceptance_values) == 1 else None,
        })

    valid = [r for r in resolved if r.get("shares") is not None]
    if not valid:
        statuses = sorted({r["status"] for r in resolved})
        return {"status": "NO_RESOLVED_CLASS_FACT", "shares": None,
                "group_statuses": statuses, "rejected": dict(rejected)}

    latest_filed = max(r["filed"] for r in valid)
    latest_invalid = max((d.isoformat() for d in invalid_asof_dates), default=None)
    if latest_invalid is not None and latest_invalid >= latest_filed:
        return {"status": "LATEST_ASOF_FILING_HAS_INVALID_SHARE_FACT", "shares": None,
                "latest_valid_filed": latest_filed, "latest_invalid_filed": latest_invalid,
                "rejected": dict(rejected)}
    latest = [r for r in valid if r["filed"] == latest_filed]
    if len(latest) > 1:
        parsed_times = [_aware_dt(r.get("acceptance_datetime")) for r in latest]
        if any(t is None for t in parsed_times):
            values = {r["shares"] for r in latest}
            if len(values) == 1:
                return {"status": "SAME_DAY_SAME_VALUE_MULTIPLE_ACCESSIONS",
                        "shares": values.pop(), "filed": latest_filed,
                        "accessions": sorted(r["accession"] for r in latest),
                        "rejected": dict(rejected)}
            return {"status": "AMBIGUOUS_SAME_DAY_VINTAGE", "shares": None,
                    "accessions": sorted(r["accession"] for r in latest),
                    "rejected": dict(rejected)}
        latest_time = max(parsed_times)
        winners = [r for r, t in zip(latest, parsed_times) if t == latest_time]
        if len(winners) > 1:
            values = {r["shares"] for r in winners}
            if len(values) == 1:
                return {"status": "SAME_DAY_SAME_VALUE_MULTIPLE_ACCESSIONS",
                        "shares": values.pop(), "filed": latest_filed,
                        "accessions": sorted(r["accession"] for r in winners),
                        "rejected": dict(rejected)}
            return {"status": "AMBIGUOUS_SAME_DAY_VINTAGE", "shares": None,
                    "accessions": sorted(r["accession"] for r in winners),
                    "rejected": dict(rejected)}
        chosen = winners[0]
    else:
        chosen = latest[0]
    return {"status": chosen["status"], "shares": chosen["shares"],
            "filed": chosen["filed"], "end": chosen["end"],
            "accession": chosen["accession"], "rejected": dict(rejected)}


def denominator_semantics() -> dict[str, str]:
    return {
        "shares_outstanding": "issuer/class total shares outstanding as of disclosed instant",
        "public_float": "market value of common equity held by non-affiliates; not a share count",
        "adv": "average daily traded share volume; not shares outstanding or float",
        "allowed_ratio_label": "proposed_units_divided_by_total_shares_outstanding",
        "forbidden_inference": "do not label this ratio float pressure or executable supply",
    }
