#!/usr/bin/env python3
"""Fail-closed SEC Schedule 13D/G event-date integrity audit.

The filing date is the only permitted historical knowledge-date field in this
module. event_date is a document-derived event descriptor and is never used
to establish public availability or signal timing.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping


def _parse_iso_date(value: object) -> date | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def classify_event_date(filing_date: object, event_date: object) -> str:
    filing = _parse_iso_date(filing_date)
    if filing is None:
        return "INVALID_OR_MISSING_FILING_DATE"
    event_text = "" if event_date is None else str(event_date).strip()
    if not event_text:
        return "MISSING_EVENT_DATE"
    event = _parse_iso_date(event_text)
    if event is None:
        return "INVALID_EVENT_DATE"
    if event > filing:
        return "AFTER_FILING_UNRESOLVED"
    if event == filing:
        return "SAME_DAY"
    return "BEFORE_FILING"


def summarize_rows(rows: Iterable[Mapping[str, object]]) -> dict:
    statuses = Counter()
    by_form = Counter()
    future_by_form = Counter()
    accessions = []
    missing_accession_rows = 0
    lag_missing_with_valid_event = 0
    total = 0

    for row in rows:
        total += 1
        form = str(row.get("form") or "UNKNOWN").strip() or "UNKNOWN"
        status = classify_event_date(row.get("filing_date"), row.get("event_date"))
        statuses[status] += 1
        by_form[form] += 1
        if status == "AFTER_FILING_UNRESOLVED":
            future_by_form[form] += 1
        if status in {"BEFORE_FILING", "SAME_DAY", "AFTER_FILING_UNRESOLVED"}:
            if not str(row.get("filing_lag_business_days") or "").strip():
                lag_missing_with_valid_event += 1
        accession = str(row.get("accession") or "").strip()
        if accession:
            accessions.append(accession)
        else:
            missing_accession_rows += 1

    unique_accessions = len(set(accessions))
    future_count = statuses["AFTER_FILING_UNRESOLVED"]
    valid_event_count = statuses["BEFORE_FILING"] + statuses["SAME_DAY"] + future_count
    return {
        "rows": total,
        "unique_accessions": unique_accessions,
        "duplicate_accession_rows": len(accessions) - unique_accessions,
        "missing_accession_rows": missing_accession_rows,
        "event_date_valid_count": valid_event_count,
        "event_date_missing_count": statuses["MISSING_EVENT_DATE"],
        "event_date_invalid_count": statuses["INVALID_EVENT_DATE"],
        "filing_date_invalid_or_missing_count": statuses["INVALID_OR_MISSING_FILING_DATE"],
        "event_date_coverage_pct": round(100 * valid_event_count / total, 2) if total else 0.0,
        "event_date_relation_counts": {
            key: statuses[key] for key in (
                "BEFORE_FILING", "SAME_DAY", "AFTER_FILING_UNRESOLVED",
                "MISSING_EVENT_DATE", "INVALID_EVENT_DATE",
                "INVALID_OR_MISSING_FILING_DATE"
            )
        },
        "future_event_rows_by_form": dict(sorted(future_by_form.items())),
        "filing_lag_business_days_missing_when_event_date_valid": lag_missing_with_valid_event,
        "form_counts": dict(sorted(by_form.items())),
        "knowledge_date_rule": "filing_date only; event_date is never a knowledge date",
        "signal_eligible": False,
        "forward_returns_used": False,
    }


def audit_csv(input_path: str | Path) -> dict:
    with open(input_path, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Input CSV is empty or has no data rows")
    required = {"form", "filing_date", "event_date", "accession"}
    missing = required.difference(rows[0].keys())
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return summarize_rows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Existing SEC 13D/G audit CSV")
    parser.add_argument("--output", required=True, help="Summary JSON output path")
    args = parser.parse_args()
    result = audit_csv(args.input)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
