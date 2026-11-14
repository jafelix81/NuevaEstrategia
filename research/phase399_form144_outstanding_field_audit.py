#!/usr/bin/env python3
"""Offline Phase 399 audit of Form 144 outstanding-share denominator integrity.

Reads only the Phase 67 issuer_event_raw.csv artifact. It does not fetch SEC data,
download prices, compute returns, infer units, or generate signals.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED = {
    "accession", "form", "filing_date", "issuer_name", "candidate_tickers",
    "sale_tranches_json",
}
THRESHOLDS = {
    "greater_than_1pct": Decimal("0.01"),
    "greater_than_10pct": Decimal("0.10"),
    "greater_than_100pct": Decimal("1"),
}


def dec(value: object) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def parse_tranches(row: dict[str, str]) -> list[dict]:
    raw = row.get("sale_tranches_json", "") or "[]"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid sale_tranches_json for {row.get('accession')}") from exc
    if not isinstance(value, list):
        raise ValueError(f"sale_tranches_json must be a list for {row.get('accession')}")
    return value


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

    forms = Counter()
    tranches = []
    for row in rows:
        forms[(row.get("form") or "").strip()] += 1
        for index, tranche in enumerate(parse_tranches(row), start=1):
            units = dec(tranche.get("units_numeric"))
            if units is None:
                units = dec(tranche.get("units_to_be_sold"))
            outstanding = dec(tranche.get("outstanding_numeric"))
            if outstanding is None:
                outstanding = dec(tranche.get("units_outstanding"))
            ratio = None
            if units is not None and outstanding is not None and outstanding > 0:
                ratio = units / outstanding
            tranches.append({
                "accession": row.get("accession", ""),
                "form": row.get("form", ""),
                "filing_date": row.get("filing_date", ""),
                "issuer": row.get("issuer_name", ""),
                "ticker_candidates": row.get("candidate_tickers", ""),
                "tranche_index": index,
                "units_to_be_sold_raw": str(tranche.get("units_to_be_sold", "")),
                "units_outstanding_raw": str(tranche.get("units_outstanding", "")),
                "units_numeric": str(units) if units is not None else None,
                "outstanding_numeric": str(outstanding) if outstanding is not None else None,
                "aggregate_market_value_raw": str(tranche.get("aggregate_market_value", "")),
                "raw_ratio_diagnostic_only": str(ratio) if ratio is not None else None,
            })

    valid_ratios = [
        Decimal(x["raw_ratio_diagnostic_only"])
        for x in tranches if x["raw_ratio_diagnostic_only"] is not None
    ]
    missing_or_zero = sum(
        1 for x in tranches
        if x["outstanding_numeric"] is None or Decimal(x["outstanding_numeric"]) <= 0
    )
    counts = {
        key: sum(1 for value in valid_ratios if value > threshold)
        for key, threshold in THRESHOLDS.items()
    }
    ordered = sorted(
        (x for x in tranches if x["raw_ratio_diagnostic_only"] is not None),
        key=lambda x: Decimal(x["raw_ratio_diagnostic_only"]),
        reverse=True,
    )
    sorted_ratios = sorted(valid_ratios)
    middle = len(sorted_ratios) // 2
    median = (
        (sorted_ratios[middle - 1] + sorted_ratios[middle]) / Decimal(2)
        if len(sorted_ratios) % 2 == 0 else sorted_ratios[middle]
    ) if sorted_ratios else None

    return {
        "phase": 399,
        "input_file": path.name,
        "issuer_event_rows": len(rows),
        "form_counts": dict(sorted(forms.items())),
        "tranche_rows": len(tranches),
        "tranches_with_missing_or_nonpositive_outstanding": missing_or_zero,
        "tranches_with_valid_raw_ratio": len(valid_ratios),
        "raw_ratio_threshold_counts": counts,
        "raw_ratio_max": str(max(valid_ratios)) if valid_ratios else None,
        "raw_ratio_median": str(median) if median is not None else None,
        "top_raw_ratio_cases": ordered[:15],
        "denominator_field": "noOfUnitsOutstanding / units_outstanding",
        "denominator_unit_metadata_present": False,
        "denominator_scale_rule_established": False,
        "raw_ratio_is_economic_percentage": False,
        "normalized_outstanding_ratio_authorized": False,
        "use_for_feature_engineering": False,
        "allowed_use": "raw field-change detection only, with source-version preservation",
        "alternative_normalization_candidate": "proposed aggregate USD value divided by lagged PIT dollar ADV, only after independent price/volume coverage and event-time gates pass",
        "forward_returns_used": False,
        "f80_changed": False,
        "holdout_used": False,
        "production_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("phase399_summary.json"))
    args = parser.parse_args()
    result = audit(args.input)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
