#!/usr/bin/env python3
"""Phase 318: independently adjudicate N-PORT filed dates against SEC business days.

Offline only. Reuses the immutable Phase 317 adjudication artifact. The SEC rule
keys the 5:30 p.m. cutoff to transmission commencement, not ACCEPTANCE-DATETIME;
therefore acceptance time is only a consistency diagnostic, never proof of
transmission start or first-public receipt.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

CUTOFF = time(17, 30)
SEC_STATUS_URL = "https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing"
SEC_RULE_URL = "https://www.ecfr.gov/current/title-17/chapter-II/part-232/section-232.13"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        last = date(year, 12, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def observed_fixed_holiday(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def us_federal_holidays(year: int) -> set[date]:
    """Federal holidays relevant to EDGAR weekday closures.

    Juneteenth is included from 2021, when it became a federal holiday.
    Good Friday is deliberately not included: it is not a federal holiday.
    """
    fixed = [
        date(year, 1, 1),       # New Year's Day
        date(year, 7, 4),       # Independence Day
        date(year, 11, 11),     # Veterans Day
        date(year, 12, 25),     # Christmas Day
    ]
    if year >= 2021:
        fixed.append(date(year, 6, 19))  # Juneteenth
    holidays = {observed_fixed_holiday(d) for d in fixed}
    holidays.update({
        nth_weekday(year, 1, 0, 3),      # Birthday of Martin Luther King, Jr.
        nth_weekday(year, 2, 0, 3),      # Washington's Birthday
        last_weekday(year, 5, 0),        # Memorial Day
        nth_weekday(year, 9, 0, 1),      # Labor Day
        nth_weekday(year, 10, 0, 2),     # Columbus Day
        nth_weekday(year, 11, 3, 4),     # Thanksgiving Day
    })
    return holidays


def edgar_holidays_for_window(year: int) -> set[date]:
    # Include adjacent years so a Saturday New Year's Day observed on Dec 31
    # of the prior year is not missed.
    return set().union(*(us_federal_holidays(y) for y in (year - 1, year, year + 1)))


def is_edgar_business_day(day: date) -> bool:
    return day.weekday() < 5 and day not in edgar_holidays_for_window(day.year)


def next_edgar_business_day(day: date) -> date:
    candidate = day + timedelta(days=1)
    for _ in range(15):
        if is_edgar_business_day(candidate):
            return candidate
        candidate += timedelta(days=1)
    raise RuntimeError(f"next_edgar_business_day_not_found:{day.isoformat()}")


def classify_clock(acceptance_datetime_et: str, filed_date: str) -> dict[str, Any]:
    accepted = datetime.strptime(acceptance_datetime_et, "%Y%m%d%H%M%S")
    filed = date.fromisoformat(filed_date)
    acceptance_date = accepted.date()
    after_cutoff = accepted.time() >= CUTOFF
    delta = (filed - acceptance_date).days
    expected_next = next_edgar_business_day(acceptance_date)
    if delta < 0:
        classification = "INVALID_FILED_DATE_PRECEDES_ACCEPTANCE_DATE"
    elif delta == 0 and after_cutoff:
        classification = "SAME_FILED_DATE_ACCEPTANCE_AFTER_1730_TRANSMISSION_START_UNOBSERVED"
    elif delta == 0:
        classification = "SAME_CALENDAR_DATE_ACCEPTANCE_BEFORE_1730"
    elif not after_cutoff:
        classification = "UNEXPLAINED_DATE_SHIFT_WITH_ACCEPTANCE_BEFORE_1730"
    elif filed == expected_next:
        classification = "NEXT_EDGAR_BUSINESS_DAY_CONSISTENT_NOT_PROOF_OF_TRANSMISSION_START"
    else:
        classification = "AFTER_1730_ACCEPTANCE_FILED_DATE_NOT_NEXT_EDGAR_BUSINESS_DAY"
    return {
        "acceptance_date": acceptance_date.isoformat(),
        "acceptance_time_et": accepted.time().isoformat(),
        "filed_date": filed.isoformat(),
        "calendar_day_shift": delta,
        "acceptance_at_or_after_1730_et": after_cutoff,
        "expected_next_edgar_business_day": expected_next.isoformat(),
        "filed_date_matches_next_edgar_business_day": filed == expected_next,
        "transmission_start_time_observed": False,
        "first_public_receipt_time_verified": False,
        "classification": classification,
    }


def adjudicate_rows(rows: list[dict[str, str]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if len(rows) != 280:
        raise ValueError(f"phase317_expected_280_rows_got:{len(rows)}")
    accessions = [r.get("accession", "") for r in rows]
    if not all(accessions) or len(set(accessions)) != len(accessions):
        raise ValueError("phase317_accessions_missing_or_duplicated")
    if any(r.get("form_type") not in {"NPORT-P", "NPORT-P/A"} for r in rows):
        raise ValueError("unexpected_form_type_in_phase317_clock_sample")
    if any(r.get("master_index_filing_date") != r.get("filed_date") for r in rows):
        raise ValueError("phase317_filed_date_master_index_mismatch")

    output = []
    for row in rows:
        clock = classify_clock(row["acceptance_datetime_et"], row["filed_date"])
        output.append({
            "accession": row["accession"],
            "quarter": row["quarter"],
            "registrant_cik": row["registrant_cik"],
            "form_type": row["form_type"],
            "report_date": row["report_date"],
            "master_index_filing_date": row["master_index_filing_date"],
            "acceptance_datetime_et": row["acceptance_datetime_et"],
            **clock,
        })

    counts = Counter(r["classification"] for r in output)
    after_cutoff = [r for r in output if r["acceptance_at_or_after_1730_et"]]
    next_day_consistent = [
        r for r in output
        if r["classification"] == "NEXT_EDGAR_BUSINESS_DAY_CONSISTENT_NOT_PROOF_OF_TRANSMISSION_START"
    ]
    same_date_after = [
        r for r in output
        if r["classification"] == "SAME_FILED_DATE_ACCEPTANCE_AFTER_1730_TRANSMISSION_START_UNOBSERVED"
    ]
    date_shifts = [r for r in output if r["calendar_day_shift"] != 0]
    shift_distribution = Counter(str(r["calendar_day_shift"]) for r in date_shifts)

    if len(after_cutoff) != 15:
        raise ValueError(f"after_cutoff_count_changed:{len(after_cutoff)}")
    if len(next_day_consistent) != 14:
        raise ValueError(f"next_business_day_consistent_count_changed:{len(next_day_consistent)}")
    if len(same_date_after) != 1:
        raise ValueError(f"same_date_after_cutoff_count_changed:{len(same_date_after)}")
    if len(date_shifts) != 14 or shift_distribution != Counter({"1": 12, "3": 2}):
        raise ValueError(f"date_shift_distribution_changed:{dict(shift_distribution)}")
    if any(r["filed_date"] != r["expected_next_edgar_business_day"] for r in next_day_consistent):
        raise ValueError("next_edgar_business_day_adjudication_failed")
    if any(r["acceptance_at_or_after_1730_et"] is False for r in date_shifts):
        raise ValueError("date_shift_before_cutoff_requires_review")
    if any(r["classification"] in {
        "INVALID_FILED_DATE_PRECEDES_ACCEPTANCE_DATE",
        "UNEXPLAINED_DATE_SHIFT_WITH_ACCEPTANCE_BEFORE_1730",
        "AFTER_1730_ACCEPTANCE_FILED_DATE_NOT_NEXT_EDGAR_BUSINESS_DAY",
    } for r in output):
        raise ValueError("unresolved_filing_clock_classification")

    result = {
        "phase": 318,
        "status": "PASS_NPORT_NEXT_EDGAR_BUSINESS_DAY_ADJUDICATION",
        "source_phase": 317,
        "source_sample_accessions": len(rows),
        "source_accessions_unique": len(set(accessions)),
        "master_index_date_matches": len(rows),
        "acceptance_calendar_date_matches_filed_date": len(rows) - len(date_shifts),
        "acceptance_at_or_after_1730_et": len(after_cutoff),
        "after_1730_acceptance_with_next_edgar_business_day_filed_date": len(next_day_consistent),
        "after_1730_acceptance_same_filed_date_unresolved": len(same_date_after),
        "date_shift_distribution_calendar_days": dict(sorted(shift_distribution.items())),
        "all_14_date_shifts_match_next_edgar_business_day": True,
        "transmission_start_time_observed": False,
        "first_public_receipt_time_verified": False,
        "nport_in_sec_10pm_exception_list": False,
        "sec_business_calendar": "Monday-Friday excluding US federal holidays, per SEC EDGAR status guidance",
        "rule_interpretation": (
            "17 CFR 232.13 uses the time direct transmission commences, not ACCEPTANCE-DATETIME. "
            "The 14 after-cutoff acceptance/date-shift rows are consistent with next-business-day filing, "
            "but do not prove when transmission commenced. The one same-filed-date acceptance after 17:30 "
            "remains unresolved and is not treated as a rule violation."
        ),
        "conservative_backtest_availability_rule": (
            "Use official FILED AS OF DATE / master-index filing date as a date-level anchor only; "
            "permit strategy use from the first full XNYS session strictly after that date. "
            "Do not use report date or acceptance timestamp as first-public time."
        ),
        "source_urls": {"sec_status_guidance": SEC_STATUS_URL, "17_cfr_232_13": SEC_RULE_URL},
        "classification_counts": dict(sorted(counts.items())),
    }
    return result, output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase317", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    source_result_path = args.phase317 / "phase317_nport_filing_clock_adjudication_result.json"
    source_rows_path = args.phase317 / "nport_clock_adjudication_rows.csv"
    source_mismatch_path = args.phase317 / "nport_acceptance_filed_date_mismatches.csv"
    if not all(p.is_file() for p in (source_result_path, source_rows_path, source_mismatch_path)):
        raise FileNotFoundError("phase317_artifact_incomplete")
    source_result = json.loads(source_result_path.read_text(encoding="utf-8"))
    if source_result.get("phase") != 317 or source_result.get("status") != "PASS_NPORT_FILING_CLOCK_AND_REPEATABILITY_ADJUDICATION":
        raise ValueError("phase317_source_result_not_pass")
    rows = read_csv(source_rows_path)
    result, adjudicated = adjudicate_rows(rows)
    mismatch_rows = read_csv(source_mismatch_path)
    source_mismatch_accessions = {r["accession"] for r in mismatch_rows}
    adjudicated_mismatch_accessions = {r["accession"] for r in adjudicated if r["calendar_day_shift"] != 0}
    if source_mismatch_accessions != adjudicated_mismatch_accessions:
        raise ValueError("phase317_mismatch_accession_set_changed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "nport_edgar_business_day_adjudication.csv", adjudicated, list(adjudicated[0].keys()))
    (args.output_dir / "phase318_nport_next_business_day_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = [
        "# Phase 318 — N-PORT next-EDGAR-business-day adjudication",
        "",
        "**Status:** PASS — offline re-adjudication of all 280 immutable Phase 316 filings through the Phase 317 artifact.",
        "",
        "## Result",
        "",
        "- 280/280 accession rows re-read; all accessions unique and all master-index filing dates match the Phase 317 FILED AS OF DATE.",
        "- 15 filings have ACCEPTANCE-DATETIME at or after 17:30 ET.",
        "- 14 have a later master-index filing date; all 14 equal the next EDGAR business day after the acceptance calendar date (12 one-day shifts and two Friday-to-Monday three-day shifts).",
        "- One filing was accepted after 17:30 ET but retains the same filed date. It remains unresolved; this is not classified as a rule violation.",
        "",
        "## Critical clock distinction",
        "",
        "17 CFR 232.13(a)(2) keys the 17:30 cutoff to when direct transmission **commences**, not to ACCEPTANCE-DATETIME. The SEC's filing-status guidance says most filings that begin transmission after 17:30 receive the next business day's filing date and are not disseminated until that next business day. Its listed 10 p.m. exceptions do not include N-PORT.",
        "",
        "Therefore the 14 rows are **consistent with** next-business-day treatment, but acceptance time does not prove transmission start. The one same-date/after-17:30 row could have commenced transmission before the cutoff and been accepted later; its transmission start is not in this sample.",
        "",
        "## Point-in-time decision",
        "",
        "- Keep master-index FILED AS OF DATE as a date-level public filing anchor, not an exact first-public timestamp.",
        "- For any later event study, allow use only from the first full XNYS session strictly after the filed date. Do not use REPORT_DATE or ACCEPTANCE-DATETIME alone as the knowledge clock.",
        "- N-PORT remains delayed holdings snapshots, not trade flow. Amendments are state corrections, not new trades.",
        "- The 280-filing sample is deterministic hash-ranked QA, not a probability sample or prevalence estimate.",
        "",
        "## Source and limitations",
        "",
        f"- SEC EDGAR filing-status guidance: {SEC_STATUS_URL}",
        f"- 17 CFR 232.13: {SEC_RULE_URL}",
        "- SEC guidance states EDGAR operates Monday–Friday except federal holidays. The offline calendar implements observed U.S. federal holidays; Good Friday is not treated as a federal holiday.",
        "- No transmission-start timestamp or exact first-public-receipt timestamp is available in the sampled submission headers.",
        "- No return, alpha, bootstrap, LOO, chronological OOS or holdout test was run.",
        "- F80, production, universe, capital and parameters remain frozen.",
        "",
        "## Source artifact",
        "",
        "- Phase 317 run 43167767387, artifact 13920996169.",
        "- Phase 317 source hashes and repeatability were validated in the upstream workflow.",
        "",
        "## Outputs",
        "",
        "- nport_edgar_business_day_adjudication.csv",
        "- phase318_nport_next_business_day_result.json",
        "- PHASE318_NPORT_NEXT_BUSINESS_DAY_ADJUDICATION_2026-11-12.md",
        "",
    ]
    (args.output_dir / "PHASE318_NPORT_NEXT_BUSINESS_DAY_ADJUDICATION_2026-11-12.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
