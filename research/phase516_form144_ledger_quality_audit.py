#!/usr/bin/env python3
"""Reproducible semantic and PIT-quality audit of the live SEC Form 144 detail ledger.

This is a descriptive data-quality audit only. It does not create signals, labels,
returns, or a backtest. In particular, a Form 144/A is not assumed to be a new
forward sale, and the formal plan-adoption field is kept separate from Remarks.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

REQUIRED = {
    "accession", "form", "issuer_cik", "detail_section", "parse_status",
    "research_observation_eligible", "public_availability_certified",
    "signal_eligible", "source_xml_hash_matches_event",
    "proposed_units_numeric", "aggregate_market_value_numeric",
    "units_outstanding_numeric", "approx_sale_date_iso",
    "approx_sale_date_relation_to_notice", "notice_date_iso",
    "plan_adoption_dates_json", "mentions_10b5_1_in_remarks",
    "nothing_to_report_flag", "prior_sale_amount_numeric",
    "first_seen_interval_lower_bound_utc",
    "first_seen_interval_upper_bound_utc", "first_seen_poll_run_id",
    "submission_acceptance_utc", "remarks", "previous_accession",
}


def truth(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def parse_date(value: Any) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_plan_dates(value: Any) -> list[date]:
    try:
        raw_dates = json.loads(str(value or "[]"))
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(raw_dates, list):
        return []
    return [d for item in raw_dates if (d := parse_date(item)) is not None]


def parse_utc(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def stats(values: list[float]) -> dict[str, float | int | None]:
    clean = sorted(float(x) for x in values)
    if not clean:
        return {"n": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None}
    def pick(p: float) -> float:
        return round(clean[int((len(clean) - 1) * p)], 10)
    return {
        "n": len(clean),
        "min": round(clean[0], 10),
        "p25": pick(0.25),
        "median": pick(0.50),
        "p75": pick(0.75),
        "max": round(clean[-1], 10),
    }


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("empty_detail_ledger")
    missing = sorted(REQUIRED - set(rows[0]))
    if missing:
        raise ValueError("required_columns_missing:" + ",".join(missing))

    by_section: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_section.setdefault(row.get("detail_section", ""), []).append(row)
    headers = by_section.get("filing_header", [])
    proposed = by_section.get("securities_information", [])
    acquisitions = by_section.get("securities_to_be_sold", [])
    prior_sales = by_section.get("securities_sold_in_past_3_months", [])
    if not headers:
        raise ValueError("filing_headers_missing")

    header_by_accession = {r["accession"]: r for r in headers}
    if len(header_by_accession) != len(headers):
        raise ValueError("duplicate_filing_header")
    prior_by_accession: dict[str, int] = {}
    acquisition_by_accession: dict[str, int] = {}
    for row in prior_sales:
        prior_by_accession[row["accession"]] = prior_by_accession.get(row["accession"], 0) + 1
    for row in acquisitions:
        acquisition_by_accession[row["accession"]] = acquisition_by_accession.get(row["accession"], 0) + 1

    plan_by_accession: dict[str, list[date]] = {}
    plan_days: list[float] = []
    future_plan_dates = 0
    for accession, row in header_by_accession.items():
        plan_dates = parse_plan_dates(row.get("plan_adoption_dates_json"))
        plan_by_accession[accession] = plan_dates
        notice = parse_date(row.get("notice_date_iso"))
        for plan_date in plan_dates:
            if notice:
                days = (notice - plan_date).days
                plan_days.append(float(days))
                if days < 0:
                    future_plan_dates += 1

    plan_accessions = {a for a, ds in plan_by_accession.items() if ds}
    remarks_accessions = {
        a for a, r in header_by_accession.items()
        if truth(r.get("mentions_10b5_1_in_remarks"))
    }
    prior_accessions = set(prior_by_accession)
    acquisition_accessions = set(acquisition_by_accession)

    ratios: list[float] = []
    complete_proposed = 0
    for row in proposed:
        try:
            units = float(row.get("proposed_units_numeric") or "")
            value = float(row.get("aggregate_market_value_numeric") or "")
            outstanding = float(row.get("units_outstanding_numeric") or "")
            sale_date = parse_date(row.get("approx_sale_date_iso"))
            if units >= 0 and value >= 0 and outstanding > 0 and sale_date:
                complete_proposed += 1
                ratios.append(units / outstanding)
        except (TypeError, ValueError):
            continue

    sale_date_relations: dict[str, int] = {}
    past_date_cases = []
    for row in proposed:
        relation = row.get("approx_sale_date_relation_to_notice") or "unknown"
        sale_date_relations[relation] = sale_date_relations.get(relation, 0) + 1
        if relation == "before_notice_date":
            header = header_by_accession.get(row["accession"], {})
            remarks = str(header.get("remarks") or "").lower()
            past_date_cases.append({
                "accession": row["accession"],
                "form": row.get("form"),
                "issuer_name": row.get("issuer_name") or header.get("issuer_name"),
                "previous_accession_present": bool(row.get("previous_accession")),
                "amendment_form": str(row.get("form") or "").upper() == "144/A",
                "remarks_explicitly_state_termination_or_no_further_sales": (
                    "terminat" in remarks and "no further sales" in remarks
                ),
            })

    no_report_mismatches = []
    for accession, header in header_by_accession.items():
        flag = str(header.get("nothing_to_report_flag") or "").strip().upper()
        has_prior = accession in prior_accessions
        if (flag == "Y" and has_prior) or (flag == "N" and not has_prior):
            no_report_mismatches.append(accession)

    interval_by_run: dict[str, list[float]] = {}
    acceptance_to_upper: list[float] = []
    malformed_intervals = 0
    for row in headers:
        lower = parse_utc(row.get("first_seen_interval_lower_bound_utc"))
        upper = parse_utc(row.get("first_seen_interval_upper_bound_utc"))
        run_id = str(row.get("first_seen_poll_run_id") or "missing")
        if lower and upper and upper >= lower:
            interval_by_run.setdefault(run_id, []).append((upper - lower).total_seconds() / 3600.0)
        else:
            malformed_intervals += 1
        acceptance = parse_utc(row.get("submission_acceptance_utc"))
        if acceptance and upper:
            acceptance_to_upper.append((upper - acceptance).total_seconds() / 3600.0)

    hash_values = [str(r.get("source_xml_hash_matches_event") or "").strip().lower() for r in rows]
    public_count = sum(truth(r.get("public_availability_certified")) for r in headers)
    signal_count = sum(truth(r.get("signal_eligible")) for r in headers)
    research_count = sum(truth(r.get("research_observation_eligible")) for r in headers)
    parse_errors = sum(str(r.get("parse_status") or "") != "parsed" for r in rows)

    result = {
        "audit": "PHASE516_SEC_FORM144_LEDGER_SEMANTICS_AND_PIT_QUALITY",
        "row_count": len(rows),
        "filing_count": len(headers),
        "issuer_cik_count": len({r.get("issuer_cik") for r in headers if r.get("issuer_cik")}),
        "form_filing_counts": {
            form: sum(str(r.get("form") or "") == form for r in headers)
            for form in sorted({str(r.get("form") or "") for r in headers})
        },
        "detail_section_counts": {k: len(v) for k, v in sorted(by_section.items())},
        "parse_error_rows": parse_errors,
        "source_hash_match_rows": sum(v == "true" for v in hash_values),
        "source_hash_mismatch_rows": sum(v == "false" for v in hash_values),
        "source_hash_not_comparable_rows": sum(v not in {"true", "false"} for v in hash_values),
        "proposed_sale": {
            "rows": len(proposed),
            "complete_rows": complete_proposed,
            "proposed_units_to_reported_class_units_outstanding_ratio": stats(ratios),
            "sale_date_relation_to_notice": dict(sorted(sale_date_relations.items())),
            "past_notice_date_cases": past_date_cases,
        },
        "prior_sales": {
            "rows": len(prior_sales),
            "filings_with_prior_sales": len(prior_accessions),
            "nothing_to_report_flag_mismatches": no_report_mismatches,
        },
        "acquisition_lots": {
            "rows": len(acquisitions),
            "filings_with_acquisition_lots": len(acquisition_accessions),
        },
        "rule_10b5_1": {
            "filings_with_formal_plan_adoption_date": len(plan_accessions),
            "formal_plan_date_entries": sum(len(v) for v in plan_by_accession.values()),
            "filings_with_10b5_1_remarks_mention": len(remarks_accessions),
            "formal_date_and_remarks_overlap": len(plan_accessions & remarks_accessions),
            "formal_date_only": len(plan_accessions - remarks_accessions),
            "remarks_only": len(remarks_accessions - plan_accessions),
            "days_from_formal_plan_date_to_notice": stats(plan_days),
            "future_plan_dates_after_notice": future_plan_dates,
        },
        "pit": {
            "research_observation_eligible_filing_headers": research_count,
            "public_availability_certified_filing_headers": public_count,
            "signal_eligible_filing_headers": signal_count,
            "malformed_or_missing_first_seen_intervals": malformed_intervals,
            "first_seen_interval_hours_by_poll_run": {
                run: stats(values) for run, values in sorted(interval_by_run.items())
            },
            "submission_acceptance_to_first_seen_upper_bound_hours": stats(acceptance_to_upper),
        },
        "controls": {
            "nothing_to_report_consistency_mismatches": len(no_report_mismatches),
            "no_signal_admitted": signal_count == 0,
            "no_public_availability_claim": public_count == 0,
            "form144a_not_assumed_to_be_new_forward_sale": True,
            "no_returns_or_backtest_performed": True,
        },
    }
    result["disposition"] = (
        "DESCRIPTIVE_LEDGER_QUALITY_PASS_WITH_SEMANTIC_REVIEW_QUEUE"
        if parse_errors == 0 and not no_report_mismatches and signal_count == 0
        else "REVIEW_REQUIRED"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="research/data/sec_form144_first_seen/sale_details.csv")
    parser.add_argument("--output", default="phase516_output/summary.json")
    args = parser.parse_args()
    with Path(args.input).open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    summary = summarize_rows(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
