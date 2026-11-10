"""Audit the historical FINRA short-interest Phase 25B/25C PIT and retrieval contract.

This is a deterministic re-adjudication of archived metadata and feature hashes.
It does not fetch live FINRA data, estimate alpha, or modify the frozen strategy.
"""
from __future__ import annotations

import calendar as pycalendar
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import exchange_calendars as xc
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "research" / "phase267_finra_short_interest_audit_input.json"
DEFAULT_OUTPUT = ROOT / "research" / "phase267_finra_short_interest_pit_pagination_audit_result.json"


def _date(value: str | date | pd.Timestamp) -> date:
    return pd.Timestamp(value).date()


def _session_date(value: Any) -> date:
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts.date()


def _sessions(cal, start: date, end: date) -> list[date]:
    return [_session_date(x) for x in cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))]


def _previous_or_same_session(cal, value: date) -> date:
    sessions = _sessions(cal, value - timedelta(days=30), value)
    if not sessions:
        raise ValueError(f"No XNYS session found on/before {value}")
    return sessions[-1]


def _first_session_on_or_after(cal, value: date) -> date:
    sessions = _sessions(cal, value, value + timedelta(days=30))
    if not sessions:
        raise ValueError(f"No XNYS session found on/after {value}")
    return sessions[0]


def _next_session_after(cal, value: date) -> date:
    sessions = _sessions(cal, value + timedelta(days=1), value + timedelta(days=30))
    if not sessions:
        raise ValueError(f"No XNYS session found after {value}")
    return sessions[0]


def _expected_settlement(cal, queried_date: date) -> date:
    """Reconstruct the scheduled mid-month or month-end settlement on XNYS."""
    if queried_date.day <= 16:
        nominal = date(queried_date.year, queried_date.month, 15)
        return _previous_or_same_session(cal, nominal)
    month_end = date(
        queried_date.year,
        queried_date.month,
        pycalendar.monthrange(queried_date.year, queried_date.month)[1],
    )
    return _previous_or_same_session(cal, month_end)


def _old_knowledge_date(settlement: date, business_days: int = 7) -> date:
    """Match pandas BDay(7): weekdays only, without exchange holidays."""
    current = settlement
    added = 0
    while added < business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def _official_publication_date(cal, settlement: date, business_days: int = 7) -> date:
    sessions = _sessions(cal, settlement + timedelta(days=1), settlement + timedelta(days=35))
    if len(sessions) < business_days:
        raise ValueError(f"Insufficient XNYS sessions after {settlement}")
    return sessions[business_days - 1]


def _session_gap(cal, old_entry: date, safe_entry: date) -> int:
    sessions = _sessions(cal, old_entry, safe_entry)
    return max(0, len(sessions) - 1)


def _latest_settlement_before(
    settlements: list[date], signal_date: date, *, official: bool, cal
) -> date | None:
    eligible = []
    for settlement in settlements:
        available = (
            _official_publication_date(cal, settlement)
            if official
            else _old_knowledge_date(settlement)
        )
        if available < signal_date:
            eligible.append(settlement)
    return max(eligible) if eligible else None


def build_result(data: dict[str, Any]) -> dict[str, Any]:
    cal = xc.get_calendar("XNYS")
    successful = sorted(_date(x) for x in data["successful_settlement_dates"])
    failed = [_date(x["queried_date"]) for x in data["retrieval"]["failed_settlement_queries"]]
    all_queries = sorted(successful + failed)

    if len(successful) != data["retrieval"]["successful_queries"]:
        raise ValueError("Successful settlement-date count does not match fixture")
    if len(failed) != data["retrieval"]["failed_queries"]:
        raise ValueError("Failed settlement-date count does not match fixture")
    if data["retrieval"]["every_successful_response_rows"] != data["official_facts"]["max_synchronous_records"]:
        raise ValueError("Fixture no longer reflects the documented synchronous API ceiling")

    schedule_mismatches = []
    for queried in all_queries:
        expected = _expected_settlement(cal, queried)
        if queried != expected:
            schedule_mismatches.append({
                "queried_date": queried.isoformat(),
                "expected_xnys_settlement": expected.isoformat(),
            })

    cycle_rows = []
    for settlement in successful:
        old_kd = _old_knowledge_date(settlement)
        publication = _official_publication_date(cal, settlement)
        old_entry = _first_session_on_or_after(cal, old_kd)
        safe_entry = _next_session_after(cal, publication)
        cycle_rows.append({
            "settlement_date": settlement.isoformat(),
            "old_knowledge_date": old_kd.isoformat(),
            "reconstructed_publication_date": publication.isoformat(),
            "old_entry_session": old_entry.isoformat(),
            "safe_next_session_entry": safe_entry.isoformat(),
            "old_entry_early_by_xnys_sessions": _session_gap(cal, old_entry, safe_entry),
            "old_knowledge_date_early": old_kd < publication,
            "old_knowledge_date_equal": old_kd == publication,
        })

    early = sum(x["old_knowledge_date_early"] for x in cycle_rows)
    equal = sum(x["old_knowledge_date_equal"] for x in cycle_rows)
    entry_gap_counts: dict[str, int] = {}
    for row in cycle_rows:
        key = str(row["old_entry_early_by_xnys_sessions"])
        entry_gap_counts[key] = entry_gap_counts.get(key, 0) + 1

    signal_audit = {}
    for phase_name in ("phase25b", "phase25c"):
        entries = []
        for signal in data[phase_name]["signal_dates"]:
            signal_day = _date(signal)
            old_latest = _latest_settlement_before(successful, signal_day, official=False, cal=cal)
            official_latest = _latest_settlement_before(successful, signal_day, official=True, cal=cal)
            entries.append({
                "signal_date": signal_day.isoformat(),
                "old_latest_settlement": old_latest.isoformat() if old_latest else None,
                "official_latest_settlement": official_latest.isoformat() if official_latest else None,
                "direct_oos_availability_mismatch": old_latest != official_latest,
            })
        signal_audit[phase_name] = entries

    request_limit = data["retrieval"]["requested_limit"]
    api_max = data["official_facts"]["max_synchronous_records"]
    page_rows = data["retrieval"]["every_successful_response_rows"]
    first_page_breaks_old_loop = page_rows < request_limit
    no_second_page = first_page_breaks_old_loop

    return {
        "phase": 267,
        "status": "INVALIDATED_PIT_AND_UNVERIFIED_HISTORICAL_COVERAGE",
        "source_artifacts": data["source"],
        "retrieval_audit": {
            "endpoint": data["retrieval"]["endpoint"],
            "successful_queries": len(successful),
            "failed_queries": len(failed),
            "all_successful_responses_at_sync_cap": page_rows == api_max,
            "requested_limit": request_limit,
            "documented_sync_max": api_max,
            "old_loop_breaks_after_first_capped_page": no_second_page,
            "record_total_header_persisted": data["retrieval"]["response_total_headers_persisted"],
            "page_offsets_observed": data["retrieval"]["page_offsets_requested"],
            "coverage_status": "UNVERIFIED_FIRST_PAGE_ONLY",
            "truncation_claim": "NOT_PROVEN_WITHOUT_RECORD_TOTAL; completeness cannot be certified",
            "required_fix": "Read Record-Total/Record-Limit/Record-Max-Limit and page until the full total is retrieved; persist headers and page hashes.",
        },
        "settlement_calendar_audit": {
            "queries": len(all_queries),
            "wrong_settlement_queries": len(schedule_mismatches),
            "mismatches": schedule_mismatches,
            "corrected_failed_cycle_dates": [
                {
                    "queried_date": x["queried_date"],
                    "expected_xnys_settlement": x["expected_xnys_settlement"],
                }
                for x in schedule_mismatches
            ],
        },
        "publication_and_execution_audit": {
            "successful_cycles": len(cycle_rows),
            "old_knowledge_date_early_cycles": early,
            "old_knowledge_date_equal_cycles": equal,
            "old_knowledge_date_late_cycles": len(cycle_rows) - early - equal,
            "old_entry_early_by_xnys_sessions_distribution": entry_gap_counts,
            "training_price_anchor_lookahead_cycles": len(cycle_rows),
            "publication_time_et": data["official_facts"]["publication_available_by_et"],
            "regular_session_close_et": "16:00",
            "safe_eod_entry_rule": "first XNYS session close strictly after the FINRA publication date",
            "cycle_detail": cycle_rows,
        },
        "signal_date_availability": signal_audit,
        "phase25c_november_2022_direct_oos_issue": data["phase25c"]["nov_25_snapshot_impact"],
        "revision_vintage_audit": data["revision_audit"],
        "original_diagnostics_not_admissible": {
            "phase25b": data["phase25b"]["results"],
            "phase25c": data["phase25c"]["results"],
            "shared_feature_file_sha256": data["source"]["shared_feature_file_sha256"],
            "independent_replication": False,
            "reason": "Both phases share the same feature file and inherit incomplete pagination, holiday-blind publication dating, and training labels anchored before the 16:40 ET data release.",
        },
        "decision": {
            "phase25b_valid_for_pit_inference": False,
            "phase25c_valid_for_pit_inference": False,
            "historical_alpha_admitted": False,
            "historical_coverage_admitted": False,
            "prospective_capture_candidate": True,
            "f80_frozen": True,
            "holdout_used": False,
            "production_changed": False,
        },
        "required_rebuild_gates": [
            "Complete every settlement-date query using response headers and deterministic pagination.",
            "Use the official FINRA publication schedule or a validated XNYS seventh-session reconstruction.",
            "For close-based execution, enter no earlier than the next XNYS session after the 16:40 ET publication date.",
            "Preserve first-receipt timestamps, raw response bytes, response headers, and correction vintages prospectively.",
            "Treat revisionFlag='R' and revised prior-cycle fields as revision evidence, not original as-published values.",
            "Resolve permanent security identity, inactive/delisted coverage, and corporate-action-adjusted prices before any return test.",
            "Only then repeat chronological training/OOS tests with identical costs and exposure; do not reuse the consumed legacy holdout.",
        ],
        "guardrails": {
            "no_live_api_calls": True,
            "no_vendor_purchase": True,
            "no_production_change": True,
            "no_universe_change": True,
            "no_f80_change": True,
            "no_holdout_use": True,
        },
    }


def run_audit(input_path: Path = DEFAULT_INPUT, output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    result = build_result(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run_audit(args.input, args.output), indent=2, sort_keys=True))
