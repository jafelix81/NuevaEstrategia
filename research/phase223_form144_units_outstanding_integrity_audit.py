#!/usr/bin/env python3
"""Phase 223: empirical integrity audit of Form 144 units-outstanding denominators."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED_CSV_SHA256 = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
EXPECTED_PANEL_ROWS = 21634
SOURCE_RUN_ID = 41959603351
SOURCE_ARTIFACT_ID = 13385365595
SOURCE_ZIP_SHA256 = "f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519"


def _decimal(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _issuer_key(value):
    s = str(value or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s.zfill(10) if s.isdigit() else s


def audit_records(rows: list[dict]) -> dict:
    tranches = []
    accessions = set()
    for row in rows:
        accession = str(row.get("accession", "")).strip()
        if not accession:
            raise ValueError("missing_accession")
        accessions.add(accession)
        raw = row.get("sale_tranches_json", "[]")
        try:
            items = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid_sale_tranches_json:{accession}") from exc
        for item in items:
            tranches.append({
                "accession": accession,
                "issuer_cik": _issuer_key(row.get("xml_issuer_cik")),
                "filing_date": str(row.get("filing_date", "")).strip(),
                "security_class": str(item.get("security_class", "")).strip().casefold(),
                "units": _decimal(item.get("units_numeric", item.get("units_to_be_sold"))),
                "value": _decimal(item.get("value_numeric", item.get("aggregate_market_value"))),
                "outstanding": _decimal(item.get("outstanding_numeric", item.get("units_outstanding"))),
            })

    if not tranches:
        raise ValueError("no_sale_tranches")

    missing = {
        "units": sum(x["units"] is None for x in tranches),
        "value": sum(x["value"] is None for x in tranches),
        "outstanding": sum(x["outstanding"] is None for x in tranches),
    }
    zero_units = sum(x["units"] == 0 for x in tranches if x["units"] is not None)
    zero_value = sum(x["value"] == 0 for x in tranches if x["value"] is not None)
    zero_outstanding = sum(x["outstanding"] == 0 for x in tranches if x["outstanding"] is not None)
    positive_small_outstanding = sum(
        x["outstanding"] is not None and 0 < x["outstanding"] < 10000 for x in tranches
    )

    ratio_gt_1pct = ratio_gt_10pct = ratio_gt_100pct = ratio_infinite = 0
    ratios = []
    for x in tranches:
        units, outstanding = x["units"], x["outstanding"]
        if units is None or outstanding is None:
            continue
        if outstanding == 0:
            if units > 0:
                ratio_infinite += 1
                ratio_gt_1pct += 1
                ratio_gt_10pct += 1
                ratio_gt_100pct += 1
            continue
        if outstanding < 0:
            continue
        ratio = units / outstanding
        ratios.append(ratio)
        ratio_gt_1pct += ratio > Decimal("0.01")
        ratio_gt_10pct += ratio > Decimal("0.10")
        ratio_gt_100pct += ratio > Decimal("1")

    groups = defaultdict(lambda: {"accessions": set(), "values": set(), "tranches": 0})
    for x in tranches:
        if not x["issuer_cik"] or not x["filing_date"] or not x["security_class"]:
            continue
        key = (x["issuer_cik"], x["security_class"], x["filing_date"])
        group = groups[key]
        group["accessions"].add(x["accession"])
        group["values"].add(x["outstanding"])
        group["tranches"] += 1

    multi_groups = [g for g in groups.values() if len(g["accessions"]) >= 2]
    conflicts = []
    for key, group in groups.items():
        if len(group["accessions"]) < 2 or len(group["values"]) <= 1:
            continue
        values = [v for v in group["values"] if v is not None]
        if len(values) <= 1:
            continue
        lo, hi = min(values), max(values)
        spread = (hi - lo) / hi if hi > 0 else None
        positive = [v for v in values if v > 0]
        scale = max(positive) / min(positive) if len(positive) >= 2 else None
        conflicts.append({
            "key": key,
            "accessions": group["accessions"],
            "tranches": group["tranches"],
            "relative_spread": spread,
            "scale_ratio": scale,
        })

    conflict_accessions = set().union(*(c["accessions"] for c in conflicts)) if conflicts else set()
    conflict_issuers = {c["key"][0] for c in conflicts}
    spread_gt_1 = sum(c["relative_spread"] is not None and c["relative_spread"] > Decimal("0.01") for c in conflicts)
    spread_gt_10 = sum(c["relative_spread"] is not None and c["relative_spread"] > Decimal("0.10") for c in conflicts)
    spread_ge_90 = sum(c["relative_spread"] is not None and c["relative_spread"] >= Decimal("0.90") for c in conflicts)
    scale_10 = sum(c["scale_ratio"] is not None and abs(c["scale_ratio"] - 10) <= Decimal("0.00001") for c in conflicts)
    scale_100 = sum(c["scale_ratio"] is not None and abs(c["scale_ratio"] - 100) <= Decimal("0.0001") for c in conflicts)
    scale_1m = sum(c["scale_ratio"] is not None and abs(c["scale_ratio"] - 1000000) <= Decimal("0.01") for c in conflicts)

    return {
        "panel_rows": len(rows),
        "unique_accessions": len(accessions),
        "tranche_rows": len(tranches),
        "missing_numeric": missing,
        "zero_values": {
            "units_to_be_sold": zero_units,
            "aggregate_market_value": zero_value,
            "units_outstanding": zero_outstanding,
        },
        "positive_units_outstanding_below_10000": positive_small_outstanding,
        "raw_sale_to_outstanding_ratio": {
            "finite_positive_denominator_rows": len(ratios),
            "infinite_rows_positive_sale_zero_outstanding": ratio_infinite,
            "ratio_gt_1pct_rows": ratio_gt_1pct,
            "ratio_gt_10pct_rows": ratio_gt_10pct,
            "ratio_gt_100pct_rows": ratio_gt_100pct,
        },
        "same_issuer_class_filing_date_reconciliation": {
            "groups_with_two_or_more_accessions": len(multi_groups),
            "groups_with_conflicting_outstanding_values": len(conflicts),
            "conflict_rate": len(conflicts) / len(multi_groups) if multi_groups else None,
            "tranches_in_conflict_groups": sum(c["tranches"] for c in conflicts),
            "unique_accessions_in_conflict_groups": len(conflict_accessions),
            "unique_issuers_in_conflict_groups": len(conflict_issuers),
            "conflict_groups_relative_spread_gt_1pct": spread_gt_1,
            "conflict_groups_relative_spread_gt_10pct": spread_gt_10,
            "conflict_groups_relative_spread_ge_90pct": spread_ge_90,
            "conflict_groups_with_approximately_10x_scale": scale_10,
            "conflict_groups_with_approximately_100x_scale": scale_100,
            "conflict_groups_with_approximately_1000000x_scale": scale_1m,
        },
        "decision": {
            "units_outstanding_admitted_as_universal_denominator": False,
            "raw_source_field_preserved": True,
            "sale_to_outstanding_ratio_admitted_as_feature": False,
            "independent_point_in_time_shares_outstanding_required": True,
            "independent_point_in_time_float_and_adv_required_for_supply_pressure": True,
            "alpha_test_authorized": False,
            "holdout_used": False,
            "f80_frozen": True,
        },
    }


def audit_csv(path: Path) -> dict:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_CSV_SHA256:
        raise ValueError("phase69_expanded_csv_sha256_mismatch")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_PANEL_ROWS:
        raise ValueError("unexpected_phase69_panel_row_count")
    result = audit_records(rows)
    if result["unique_accessions"] != EXPECTED_PANEL_ROWS:
        raise ValueError("duplicate_or_missing_accessions")
    result["source"] = {
        "run_id": SOURCE_RUN_ID,
        "artifact_id": SOURCE_ARTIFACT_ID,
        "artifact_zip_sha256": SOURCE_ZIP_SHA256,
        "member": "expanded_issuer_event_raw.csv",
        "csv_sha256": digest,
        "csv_bytes": len(raw),
    }
    result["phase"] = 223
    result["status"] = "FORM144_UNITS_OUTSTANDING_NOT_ADMITTED_AS_DENOMINATOR"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_csv(args.input_csv)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
