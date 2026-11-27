#!/usr/bin/env python3
"""Exact accession-level join of Form 144 plan dates to first-seen PIT status.

Descriptive audit only. It does not infer execution, public-release time, or alpha.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_EVENTS = Path("research/data/sec_form144_first_seen/events.csv")
DEFAULT_DETAILS = Path("research/data/sec_form144_first_seen/sale_details.csv")

PIT_FIELDS = (
    "research_observation_eligible",
    "public_availability_certified",
    "signal_eligible",
    "first_seen_interval_status",
    "first_seen_interval_lower_bound_utc",
    "first_seen_interval_upper_bound_utc",
)
DETAIL_CONSISTENCY_FIELDS = (
    "plan_adoption_dates_json",
    "form",
    "issuer_cik",
    "issuer_name",
    "seller_name",
    "notice_date_iso",
    "remarks",
    "mentions_10b5_1_in_remarks",
    *PIT_FIELDS,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "accession" not in reader.fieldnames:
            raise ValueError(f"missing_accession_column:{path}")
        rows = list(reader)
    if any(not str(row.get("accession") or "").strip() for row in rows):
        raise ValueError(f"blank_accession:{path}")
    return rows


def group_by_accession(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["accession"]).strip()].append(row)
    return dict(grouped)


def consistent_value(rows: list[dict[str, str]], field: str, accession: str) -> str:
    values = {str(row.get(field) or "").strip() for row in rows}
    if len(values) != 1:
        raise ValueError(f"inconsistent_{field}:{accession}:{sorted(values)!r}")
    return next(iter(values))


def parse_bool(value: str, *, field: str, accession: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"invalid_boolean_{field}:{accession}:{value!r}")


def parse_plan_dates(raw: str, accession: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_plan_adoption_dates_json:{accession}") from exc
    if not isinstance(value, list):
        raise ValueError(f"plan_adoption_dates_not_list:{accession}")
    dates = sorted({str(item).strip() for item in value if str(item).strip()})
    return dates


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_summary(events_path: Path, details_path: Path) -> dict[str, Any]:
    event_rows = read_csv(events_path)
    detail_rows = read_csv(details_path)
    events = group_by_accession(event_rows)
    details = group_by_accession(detail_rows)

    detail_pit_conflicts = 0
    crossledger_mismatches: list[dict[str, str]] = []
    plan_date_accessions = 0
    plan_date_pit_overlap = 0
    plan_date_baseline = 0
    eligible_accessions = 0
    baseline_accessions = 0
    public_certified_accessions = 0
    signal_eligible_accessions = 0
    plan_dates: set[str] = set()
    plan_by_form: Counter[str] = Counter()
    plan_by_status: Counter[str] = Counter()

    for accession, rows in details.items():
        values = {
            field: consistent_value(rows, field, accession)
            for field in DETAIL_CONSISTENCY_FIELDS
        }
        dates = parse_plan_dates(values["plan_adoption_dates_json"], accession)
        status = values["first_seen_interval_status"]
        research = parse_bool(values["research_observation_eligible"], field="research_observation_eligible", accession=accession)
        public = parse_bool(values["public_availability_certified"], field="public_availability_certified", accession=accession)
        signal = parse_bool(values["signal_eligible"], field="signal_eligible", accession=accession)

        if status == "INITIAL_BASELINE_NO_LOWER_BOUND":
            baseline_accessions += 1
            if research:
                raise ValueError(f"baseline_marked_research_eligible:{accession}")
        if research:
            eligible_accessions += 1
        if public:
            public_certified_accessions += 1
        if signal:
            signal_eligible_accessions += 1

        event_group = events.get(accession)
        if not event_group:
            crossledger_mismatches.append({"accession": accession, "field": "missing_event_accession"})
        else:
            for field in PIT_FIELDS:
                detail_value = values[field]
                event_values = {str(row.get(field) or "").strip() for row in event_group}
                if event_values != {detail_value}:
                    crossledger_mismatches.append({
                        "accession": accession,
                        "field": field,
                        "detail_value": detail_value,
                        "event_values": json.dumps(sorted(event_values), ensure_ascii=False),
                    })

        if dates:
            plan_date_accessions += 1
            plan_dates.update(dates)
            plan_by_form[values["form"] or "UNKNOWN"] += 1
            plan_by_status[status or "UNKNOWN"] += 1
            if research:
                plan_date_pit_overlap += 1
            if status == "INITIAL_BASELINE_NO_LOWER_BOUND":
                plan_date_baseline += 1

    if detail_pit_conflicts:
        raise ValueError("unexpected_detail_pit_conflicts")
    if crossledger_mismatches:
        sample = crossledger_mismatches[:5]
        raise ValueError(f"crossledger_pit_mismatch:{sample!r}")

    event_only_accessions = sorted(set(events) - set(details))
    detail_only_accessions = sorted(set(details) - set(events))
    if detail_only_accessions:
        raise ValueError(f"detail_accessions_missing_from_event_ledger:{detail_only_accessions[:10]!r}")

    no_plan_eligible = eligible_accessions - plan_date_pit_overlap
    no_plan_baseline = baseline_accessions - plan_date_baseline
    denominator = len(details)

    def pct(numerator: int, denominator_value: int) -> float | None:
        return round(100.0 * numerator / denominator_value, 2) if denominator_value else None

    return {
        "phase": 665,
        "audit": "FORM144_ACCESSION_LEVEL_PLAN_DATE_TO_PIT_JOIN",
        "source_files": {
            "events": {
                "path": str(events_path),
                "rows": len(event_rows),
                "unique_accessions": len(events),
                "sha256": sha256_file(events_path),
            },
            "sale_details": {
                "path": str(details_path),
                "rows": len(detail_rows),
                "unique_accessions": len(details),
                "sha256": sha256_file(details_path),
            },
        },
        "counts": {
            "structured_detail_accessions": denominator,
            "research_observation_eligible_accessions": eligible_accessions,
            "initial_baseline_no_lower_bound_accessions": baseline_accessions,
            "formal_plan_date_accessions": plan_date_accessions,
            "formal_plan_date_and_research_observation_eligible_accessions": plan_date_pit_overlap,
            "formal_plan_date_and_initial_baseline_accessions": plan_date_baseline,
            "research_observation_eligible_without_plan_date": no_plan_eligible,
            "initial_baseline_without_plan_date": no_plan_baseline,
            "public_availability_certified_accessions": public_certified_accessions,
            "signal_eligible_accessions": signal_eligible_accessions,
            "event_accessions_without_structured_details": len(event_only_accessions),
            "structured_detail_accessions_without_event": len(detail_only_accessions),
            "distinct_formal_plan_adoption_dates": len(plan_dates),
        },
        "formal_plan_date_accessions_by_form": dict(sorted(plan_by_form.items())),
        "formal_plan_date_accessions_by_pit_status": dict(sorted(plan_by_status.items())),
        "rates_pct": {
            "plan_date_accessions_within_all_structured_details": pct(plan_date_accessions, denominator),
            "plan_date_accessions_within_research_observation_eligible": pct(plan_date_pit_overlap, eligible_accessions),
            "research_observation_eligible_share_of_plan_date_cohort": pct(plan_date_pit_overlap, plan_date_accessions),
            "baseline_share_of_plan_date_cohort": pct(plan_date_baseline, plan_date_accessions),
        },
        "integrity": {
            "detail_accession_fields_checked": list(DETAIL_CONSISTENCY_FIELDS),
            "crossledger_pit_fields_checked": list(PIT_FIELDS),
            "detail_accession_consistency_conflicts": 0,
            "crossledger_pit_mismatches": 0,
            "all_structured_detail_accessions_present_in_event_ledger": True,
            "event_only_accessions_are_not_in_plan_date_denominator": True,
        },
        "limitations": {
            "event_only_accessions_have_no_structured_plan_date_classification": len(event_only_accessions),
            "first_seen_upper_bound_is_not_exact_public_release_time": True,
            "research_observation_eligibility_is_not_signal_eligibility": True,
            "form144_is_proposed_sale_notice_not_execution_confirmation": True,
            "formal_plan_date_does_not_prove_execution_or_discretionary_intent": True,
        },
        "controls": {
            "return_data_inspected": False,
            "event_study_run": False,
            "alpha_test_run": False,
            "chronological_oos_run": False,
            "bootstrap_run": False,
            "loo_run": False,
            "holdout_used": False,
            "signal_admitted": False,
            "f80_top20_partial50_baseline_c20_frozen": True,
            "vendor_contact": False,
            "data_purchase": False,
            "data_budget_usd": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--details", type=Path, default=DEFAULT_DETAILS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = build_summary(args.events, args.details)
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
