#!/usr/bin/env python3
"""Offline Phase 398 audit: Form 144/A lineage and tranche-level issuer security mapping.

This script never fetches SEC data, downloads prices, computes returns, or generates signals.
It operates only on the Phase 67 issuer_event_raw.csv artifact.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = {
    "accession", "form", "filing_date", "candidate_tickers",
    "candidate_ciks_in_pair", "xml_issuer_cik", "xml_filer_cik",
    "issuer_name", "seller_name", "previous_accession_normalized",
    "previous_accession_in_14q_census", "sale_tranche_count",
    "sale_tranches_json",
}

ZILLOW_CIK = "0001617640"
ASTS_CIK = "0001780312"
AMT_CIK = "0001053507"


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def canonical_class(value: object) -> str:
    s = clean(value).casefold()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    m = re.search(r"\bclass\s+([abc])\b", s)
    if m:
        return f"class {m.group(1)}"
    m = re.search(r"\bcommon\s+class\s+([abc])\b", s)
    if m:
        return f"class {m.group(1)}"
    return s


def parse_tranches(row: dict[str, str]) -> list[dict]:
    raw = row.get("sale_tranches_json", "") or "[]"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid sale_tranches_json for {row.get('accession')}") from exc
    if not isinstance(value, list):
        raise ValueError(f"sale_tranches_json must be a list for {row.get('accession')}")
    return value


def dec(value: object) -> Decimal | None:
    try:
        if value is None or clean(value) == "":
            return None
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def aggregate_by_class(tranches: list[dict], field: str) -> dict[str, Decimal | None]:
    out: dict[str, Decimal | None] = {}
    for t in tranches:
        key = canonical_class(t.get("security_class"))
        value = dec(t.get(field))
        if key not in out:
            out[key] = value
        elif value is None or out[key] is None:
            out[key] = None
        else:
            out[key] += value
    return out


def same_numeric_map(a: dict, b: dict) -> bool:
    if set(a) != set(b):
        return False
    for key in a:
        if a[key] is None or b[key] is None:
            if a[key] is not b[key]:
                return False
        elif a[key] != b[key]:
            return False
    return True


def class_set(tranches: list[dict]) -> set[str]:
    return {canonical_class(t.get("security_class")) for t in tranches}


def ticker_map_for_ambiguous_row(row: dict[str, str]) -> list[dict]:
    """Resolve only the two audited candidate-pair patterns; leave generic classes unresolved."""
    candidates = [x for x in clean(row.get("candidate_tickers")).split(";") if x]
    ciks = [x for x in clean(row.get("candidate_ciks_in_pair")).split(";") if x]
    issuer_cik = clean(row.get("xml_issuer_cik"))
    tranches = parse_tranches(row)
    out = []

    if set(candidates) == {"Z", "ZG"} and issuer_cik == ZILLOW_CIK:
        for i, tranche in enumerate(tranches, start=1):
            cls = canonical_class(tranche.get("security_class"))
            ticker = {"class c": "Z", "class a": "ZG"}.get(cls)
            out.append({
                "tranche_index": i,
                "security_class": clean(tranche.get("security_class")),
                "ticker": ticker,
                "status": "resolved_by_issuer_class" if ticker else "unresolved_generic_class",
            })
        return out

    if set(candidates) == {"AMT", "ASTS"} and issuer_cik == ASTS_CIK and AMT_CIK in ciks:
        for i, tranche in enumerate(tranches, start=1):
            out.append({
                "tranche_index": i,
                "security_class": clean(tranche.get("security_class")),
                "ticker": "ASTS",
                "status": "issuer_side_cik_resolution_subject_to_effective_crosswalk",
            })
        return out

    for i, tranche in enumerate(tranches, start=1):
        out.append({
            "tranche_index": i,
            "security_class": clean(tranche.get("security_class")),
            "ticker": None,
            "status": "unresolved_no_audited_rule",
        })
    return out


def audit(path: Path) -> dict:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        rows = list(reader)
    if not rows:
        raise ValueError("empty input")

    by_accession: dict[str, dict[str, str]] = {}
    duplicate_accessions = 0
    for row in rows:
        accession = clean(row.get("accession"))
        if accession in by_accession:
            duplicate_accessions += 1
        by_accession[accession] = row

    forms = Counter(clean(r.get("form")) for r in rows)
    amendments = [r for r in rows if clean(r.get("form")) == "144/A"]
    parent_status = Counter()
    parent_form = Counter()
    changed = Counter()
    matched_parent_count = 0
    parent_date_inversions = 0
    cik_mismatches = 0
    chain_depths = Counter()
    cycles = 0
    exact_payload_unchanged = 0
    z_rows = z_tranches = zg_tranches = generic_zillow_rows = 0
    asts_issuer_rows = 0
    resolution_status = Counter()
    zillow_tranche_classes = Counter()

    parent_map: dict[str, str] = {}
    for row in amendments:
        acc = clean(row.get("accession"))
        parent = clean(row.get("previous_accession_normalized"))
        if parent:
            parent_map[acc] = parent
        p = by_accession.get(parent)
        if not parent or p is None:
            if clean(row.get("previous_accession_in_14q_census")).casefold() == "true":
                parent_status["in_14q_census_not_in_candidate_panel"] += 1
            else:
                parent_status["outside_census_or_missing"] += 1
            continue

        matched_parent_count += 1
        parent_status["matched_in_candidate_panel"] += 1
        parent_form[clean(p.get("form"))] += 1

        try:
            if date.fromisoformat(clean(p.get("filing_date"))) > date.fromisoformat(clean(row.get("filing_date"))):
                parent_date_inversions += 1
        except ValueError:
            parent_date_inversions += 1

        if clean(p.get("xml_issuer_cik")) != clean(row.get("xml_issuer_cik")) or clean(p.get("xml_filer_cik")) != clean(row.get("xml_filer_cik")):
            cik_mismatches += 1

        pt = parse_tranches(p)
        at = parse_tranches(row)
        field_equal = {
            "tranche_count_changed": len(pt) != len(at),
            "class_set_changed": class_set(pt) != class_set(at),
            "units_changed": not same_numeric_map(aggregate_by_class(pt, "units_numeric"), aggregate_by_class(at, "units_numeric")),
            "value_changed": not same_numeric_map(aggregate_by_class(pt, "value_numeric"), aggregate_by_class(at, "value_numeric")),
            "outstanding_changed": not same_numeric_map(aggregate_by_class(pt, "outstanding_numeric"), aggregate_by_class(at, "outstanding_numeric")),
            "sale_date_changed": sorted(clean(t.get("approx_sale_date_iso")) for t in pt) != sorted(clean(t.get("approx_sale_date_iso")) for t in at),
            "broker_changed": sorted(clean(t.get("broker_or_market_maker")).casefold() for t in pt) != sorted(clean(t.get("broker_or_market_maker")).casefold() for t in at),
            "exchange_changed": sorted(clean(t.get("exchange")).casefold() for t in pt) != sorted(clean(t.get("exchange")).casefold() for t in at),
        }
        for name, is_changed in field_equal.items():
            if is_changed:
                changed[name] += 1
        if not any(field_equal.values()):
            exact_payload_unchanged += 1

    for row in amendments:
        acc = clean(row.get("accession"))
        cur = acc
        seen = set()
        depth = 0
        while cur in parent_map and parent_map[cur] in by_accession:
            if cur in seen:
                cycles += 1
                break
            seen.add(cur)
            cur = parent_map[cur]
            depth += 1
        chain_depths[str(depth)] += 1

    ambiguous_rows = [r for r in rows if ";" in clean(r.get("candidate_tickers"))]
    for row in ambiguous_rows:
        candidates = set(x for x in clean(row.get("candidate_tickers")).split(";") if x)
        if candidates == {"Z", "ZG"} and clean(row.get("xml_issuer_cik")) == ZILLOW_CIK:
            z_rows += 1
            resolved = ticker_map_for_ambiguous_row(row)
            if any(x["ticker"] is None for x in resolved):
                generic_zillow_rows += 1
            for item in resolved:
                zillow_tranche_classes[canonical_class(item["security_class"])] += 1
                if item["ticker"] == "Z":
                    z_tranches += 1
                elif item["ticker"] == "ZG":
                    zg_tranches += 1
                resolution_status[item["status"]] += 1
        elif candidates == {"AMT", "ASTS"} and clean(row.get("xml_issuer_cik")) == ASTS_CIK:
            asts_issuer_rows += 1
            for item in ticker_map_for_ambiguous_row(row):
                resolution_status[item["status"]] += 1
        else:
            resolution_status["unresolved_other_pair"] += 1

    return {
        "phase": 398,
        "input_file": path.name,
        "row_count": len(rows),
        "duplicate_accessions": duplicate_accessions,
        "form_counts": dict(sorted(forms.items())),
        "amendment_count": len(amendments),
        "amendment_parent_status": dict(sorted(parent_status.items())),
        "matched_parent_form_counts": dict(sorted(parent_form.items())),
        "matched_parent_count": matched_parent_count,
        "amendments_with_exactly_unchanged_tranche_payload": exact_payload_unchanged,
        "amendment_payload_change_counts": dict(sorted(changed.items())),
        "parent_date_inversions": parent_date_inversions,
        "issuer_or_filer_cik_mismatches": cik_mismatches,
        "amendment_chain_depth_counts": dict(sorted(chain_depths.items(), key=lambda x: int(x[0]))),
        "amendment_chain_cycles": cycles,
        "ambiguous_ticker_rows": len(ambiguous_rows),
        "zillow_issuer_rows": z_rows,
        "zillow_class_c_tranches_resolved_to_Z": z_tranches,
        "zillow_class_a_tranches_resolved_to_ZG": zg_tranches,
        "zillow_generic_class_rows_unresolved": generic_zillow_rows,
        "zillow_tranche_class_counts": dict(sorted(zillow_tranche_classes.items())),
        "asts_issuer_side_rows": asts_issuer_rows,
        "ticker_resolution_status_counts": dict(sorted(resolution_status.items())),
        "amendments_are_independent_sale_events": False,
        "amendments_must_be_versioned_at_own_filing_date": True,
        "economic_test_authorized": False,
        "forward_returns_used": False,
        "f80_changed": False,
        "production_changed": False,
        "holdout_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("phase398_summary.json"))
    args = parser.parse_args()
    result = audit(args.input)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
