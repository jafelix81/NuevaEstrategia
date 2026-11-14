#!/usr/bin/env python3
"""Reproducible, offline integrity audit for a Phase 67 Form 144 event CSV."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

REQUIRED = {
    "accession", "form", "filing_date", "notice_date", "candidate_tickers",
    "candidate_role_status", "xml_issuer_cik", "xml_filer_cik", "issuer_name",
    "seller_name", "sale_tranche_count", "sale_units_total", "sale_value_total",
    "sale_units_all_numeric", "sale_value_all_numeric", "sale_outstanding_all_numeric",
    "sale_tranches_json", "previous_accession", "previous_accession_in_14q_census",
    "mentions_10b5_1", "plan_adoption_dates",
}

def parse_date(value: str, fmt: str):
    return datetime.strptime(value.strip(), fmt).date()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def audit(path: Path) -> dict:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        rows = list(reader)
    if not rows:
        raise ValueError("empty event file")
    accessions = [r["accession"].strip() for r in rows]
    duplicate_accessions = len(accessions) - len(set(accessions))
    forms = Counter(r["form"].strip() for r in rows)
    notice_delta = Counter()
    invalid_dates = 0
    multi_ticker_rows = []
    zero_units_events = zero_value_events = zero_outstanding_events = 0
    zero_units_tranches = zero_value_tranches = zero_outstanding_tranches = 0
    multi_tranche_events = 0
    flag_10b5 = 0
    amendment_rows = 0
    amendment_parent_in_census = 0
    for r in rows:
        try:
            filed = parse_date(r["filing_date"], "%Y-%m-%d")
            notice = parse_date(r["notice_date"], "%m/%d/%Y")
            notice_delta[(notice - filed).days] += 1
        except Exception:
            invalid_dates += 1
        tickers = [x.strip() for x in r["candidate_tickers"].split(";") if x.strip()]
        if len(set(tickers)) > 1:
            multi_ticker_rows.append(r)
        try:
            tranches = json.loads(r["sale_tranches_json"] or "[]")
        except Exception as e:
            raise ValueError(f"invalid sale_tranches_json for {r['accession']}") from e
        if len(tranches) > 1:
            multi_tranche_events += 1
        event_zero_units = event_zero_value = event_zero_outstanding = False
        for t in tranches:
            try:
                units = float(t.get("units_numeric"))
                if units <= 0:
                    zero_units_tranches += 1
                    event_zero_units = True
            except (TypeError, ValueError):
                zero_units_tranches += 1
                event_zero_units = True
            try:
                value = float(t.get("value_numeric"))
                if value <= 0:
                    zero_value_tranches += 1
                    event_zero_value = True
            except (TypeError, ValueError):
                zero_value_tranches += 1
                event_zero_value = True
            try:
                outstanding = float(t.get("outstanding_numeric"))
                if outstanding <= 0:
                    zero_outstanding_tranches += 1
                    event_zero_outstanding = True
            except (TypeError, ValueError):
                zero_outstanding_tranches += 1
                event_zero_outstanding = True
        zero_units_events += int(event_zero_units)
        zero_value_events += int(event_zero_value)
        zero_outstanding_events += int(event_zero_outstanding)
        flag_10b5 += int(str(r["mentions_10b5_1"]).strip().lower() == "true")
        if r["form"].strip() == "144/A":
            amendment_rows += 1
            amendment_parent_in_census += int(str(r["previous_accession_in_14q_census"]).strip().lower() == "true")
    multi_ticker_groups = Counter(
        ";".join(sorted({x.strip() for x in r["candidate_tickers"].split(";") if x.strip()}))
        for r in multi_ticker_rows
    )
    z_zg = [
        r for r in multi_ticker_rows
        if set(x.strip() for x in r["candidate_tickers"].split(";")) == {"Z", "ZG"}
    ]
    z_zg_classes = Counter()
    for r in z_zg:
        tranches = json.loads(r["sale_tranches_json"] or "[]")
        classes = sorted({
            str(t.get("security_class") or "").strip()
            for t in tranches if str(t.get("security_class") or "").strip()
        })
        z_zg_classes["|".join(classes) if classes else "<missing>"] += 1
    acceptance_columns = [
        c for c in fields
        if any(k in c.lower() for k in ("acceptance", "accepted_timestamp", "accepted_datetime"))
    ]
    return {
        "phase": 397,
        "input_file": path.name,
        "input_sha256": sha256_file(path),
        "row_count": len(rows),
        "duplicate_accessions": duplicate_accessions,
        "form_counts": dict(sorted(forms.items())),
        "notice_vs_filing_date_delta_days": {str(k): v for k, v in sorted(notice_delta.items())},
        "notice_date_mismatch_rows": sum(v for k, v in notice_delta.items() if k != 0),
        "notice_date_earlier_than_filing_rows": sum(v for k, v in notice_delta.items() if k < 0),
        "notice_date_later_than_filing_rows": sum(v for k, v in notice_delta.items() if k > 0),
        "invalid_date_rows": invalid_dates,
        "accepted_timestamp_columns": acceptance_columns,
        "accepted_timestamp_gate": "NOT_TESTED_NOT_PRESENT_IN_PHASE67_EVENT_CSV" if not acceptance_columns else "COLUMN_PRESENT_REQUIRES_ROW_COVERAGE_AUDIT",
        "multi_candidate_ticker_rows": len(multi_ticker_rows),
        "multi_candidate_ticker_groups": dict(multi_ticker_groups),
        "z_zg_multi_candidate_rows": len(z_zg),
        "z_zg_security_class_event_groups": dict(z_zg_classes),
        "multi_tranche_events": multi_tranche_events,
        "zero_or_invalid_units_events": zero_units_events,
        "zero_or_invalid_value_events": zero_value_events,
        "zero_or_invalid_outstanding_events": zero_outstanding_events,
        "zero_or_invalid_units_tranches": zero_units_tranches,
        "zero_or_invalid_value_tranches": zero_value_tranches,
        "zero_or_invalid_outstanding_tranches": zero_outstanding_tranches,
        "form144a_rows": amendment_rows,
        "form144a_parent_reference_in_census": amendment_parent_in_census,
        "form144a_parent_reference_not_in_census": amendment_rows - amendment_parent_in_census,
        "mentions_10b5_1_rows": flag_10b5,
        "economic_test_authorized": False,
        "forward_returns_used": False,
        "f80_changed": False,
        "production_changed": False,
        "holdout_used": False,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", type=Path, default=Path("phase397_summary.json"))
    a = p.parse_args()
    result = audit(a.input)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
