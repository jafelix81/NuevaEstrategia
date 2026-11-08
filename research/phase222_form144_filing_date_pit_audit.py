#!/usr/bin/env python3
"""Phase 222: conservative Form 144 daily PIT clock audit."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from bisect import bisect_right
from collections import Counter
from datetime import date, datetime, timedelta
from importlib.metadata import version
from pathlib import Path

EVIDENCE = Path(__file__).with_name("phase222_form144_filing_date_pit_audit.json")
EXPECTED_CSV_SHA256 = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
PILOT = [
    {
        "ticker": "PINS",
        "accession": "0001921094-26-000697",
        "accepted_date": "2026-07-01",
        "next_session": "2026-07-02"
    },
    {
        "ticker": "SCHW",
        "accession": "0001949846-26-000451",
        "accepted_date": "2026-07-29",
        "next_session": "2026-07-30"
    },
    {
        "ticker": "SNOW",
        "accession": "0001959173-26-005295",
        "accepted_date": "2026-07-21",
        "next_session": "2026-07-22"
    },
    {
        "ticker": "ANET",
        "accession": "0001959173-26-006426",
        "accepted_date": "2026-08-25",
        "next_session": "2026-08-26"
    },
    {
        "ticker": "RUN",
        "accession": "0001921094-26-000789",
        "accepted_date": "2026-08-03",
        "next_session": "2026-08-04"
    }
]


def next_session_after(filing_date: str, session_dates: list[str]) -> str:
    """Return the first XNYS session strictly after the SEC filing date."""
    i = bisect_right(session_dates, filing_date)
    if i >= len(session_dates):
        raise ValueError("calendar_does_not_cover_next_session")
    return session_dates[i]


def _truth(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def audit_csv(path: Path) -> dict:
    import exchange_calendars as xc
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_CSV_SHA256:
        raise ValueError("phase69_expanded_csv_sha256_mismatch")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 21634:
        raise ValueError("unexpected_phase69_panel_row_count")
    accessions = [r["accession"] for r in rows]
    if len(set(accessions)) != len(accessions):
        raise ValueError("duplicate_accession")
    dates = []
    for row in rows:
        if not row.get("filing_date"):
            raise ValueError("missing_master_index_filing_date")
        dates.append(date.fromisoformat(row["filing_date"]))
    dmin, dmax = min(dates), max(dates)
    cal = xc.get_calendar("XNYS")
    sessions = cal.sessions_in_range(dmin.isoformat(), (dmax + timedelta(days=15)).isoformat())
    session_dates = sorted(str(s.date()) for s in sessions)
    session_set = set(session_dates)
    if any(d.weekday() >= 5 for d in dates):
        raise ValueError("weekend_filing_date")
    if any(d.isoformat() not in session_set for d in dates):
        raise ValueError("filing_date_not_xnys_session")
    unique_dates = sorted({d.isoformat() for d in dates})
    mapping = {d: next_session_after(d, session_dates) for d in unique_dates}

    role_counts = Counter(r["candidate_role_status"] for r in rows)
    form_counts = Counter(r["form"] for r in rows)
    ticker_count = len({r["candidate_tickers"] for r in rows if r.get("candidate_tickers")})
    issuer_count = len({r["xml_issuer_cik"] for r in rows if r.get("xml_issuer_cik")})
    notice_lags = []
    for row, filed in zip(rows, dates):
        raw_notice = row.get("notice_date", "")
        if raw_notice:
            notice = datetime.strptime(raw_notice, "%m/%d/%Y").date()
            notice_lags.append((notice - filed).days)
    diff_n = sum(x != 0 for x in notice_lags)

    amendment_rows = [r for r in rows if r["form"] == "144/A"]
    amendment_parent_n = sum(bool(r.get("previous_accession")) for r in amendment_rows)
    parent_in_census_n = sum(_truth(r.get("previous_accession_in_14q_census", "")) for r in amendment_rows)

    pilot_results = []
    by_accession = {r["accession"]: r for r in rows}
    for p in PILOT:
        row = by_accession[p["accession"]]
        filed = row["filing_date"]
        next_day = mapping[filed]
        pilot_results.append({
            "ticker": p["ticker"],
            "filing_date_matches_acceptance_date": filed == p["accepted_date"],
            "next_session_matches": next_day == p["next_session"]
        })
    if not all(x["filing_date_matches_acceptance_date"] and x["next_session_matches"] for x in pilot_results):
        raise ValueError("phase211_acceptance_pilot_mismatch")

    early_close_n = 0
    for d in unique_dates:
        s = next_session_after(d, session_dates)
        session = next(x for x in sessions if str(x.date()) == s)
        duration = (cal.session_close(session) - cal.session_open(session)).total_seconds() / 60
        if duration < 390:
            early_close_n += 1

    return {
        "source_csv_sha256": digest,
        "rows": len(rows),
        "unique_accessions": len(set(accessions)),
        "role_counts": dict(role_counts),
        "form_counts": dict(form_counts),
        "unique_issuer_ciks": issuer_count,
        "unique_current_tickers_with_events": ticker_count,
        "filing_date_min": dmin.isoformat(),
        "filing_date_max": dmax.isoformat(),
        "filing_date_missing": 0,
        "unique_filing_dates": len(unique_dates),
        "weekend_rows": 0,
        "non_xnys_filing_date_rows": 0,
        "next_session_mappings": len(mapping),
        "next_session_missing": 0,
        "next_session_early_close_count": early_close_n,
        "notice_date_differs_from_filing_date_rows": diff_n,
        "notice_date_lag_min": min(notice_lags),
        "notice_date_lag_max": max(notice_lags),
        "amendments_with_previous_accession": amendment_parent_n,
        "amendments_parent_inside_census": parent_in_census_n,
        "acceptance_pilot": pilot_results,
        "calendar_library_version": version("exchange-calendars"),
        "daily_pit_clock_admitted": True,
        "full_signal_panel_admitted": False
    }


def build_audit(e: dict) -> dict:
    if e.get("phase") != 222:
        raise ValueError("unexpected_phase")
    p = e["panel"]
    if p["rows"] != 21634 or p["unique_accessions"] != 21634:
        raise ValueError("panel_integrity_changed")
    if p["filing_date_missing"] != 0 or p["unique_filing_dates"] != 861:
        raise ValueError("filing_date_coverage_changed")
    if p["clean_issuer_match_rows"] != 21633 or p["ambiguous_issuer_match_rows"] != 1:
        raise ValueError("issuer_role_quarantine_changed")
    if e["calendar"]["filing_dates_mapped"] != 861 or e["calendar"]["next_session_missing"] != 0:
        raise ValueError("calendar_mapping_incomplete")
    if e["acceptance_pilot"]["verified_pairs"] != 5 or e["acceptance_pilot"]["filing_date_matches_acceptance_date"] != 5 or e["acceptance_pilot"]["next_session_matches"] != 5:
        raise ValueError("acceptance_pilot_not_reproduced")
    if e["decision"]["daily_pit_clock_admitted"] is not True:
        raise ValueError("daily_pit_clock_not_admitted")
    if e["decision"]["full_signal_panel_admitted"] is not False or e["decision"]["alpha_test_authorized"] is not False:
        raise ValueError("premature_signal_admission")
    if e["decision"]["f80_frozen"] is not True or e["decision"]["holdout_used"] is not False:
        raise ValueError("frozen_controls_changed")
    return {
        "phase": 222,
        "status": e["status"],
        "daily_pit_clock_admitted": True,
        "first_eligible_session_rule": "FIRST_XNYS_SESSION_OPEN_STRICTLY_AFTER_SEC_MASTER_INDEX_FILING_DATE",
        "same_day_use": False,
        "intraday_admitted": False,
        "full_signal_panel_admitted": False,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "decision": "PROCEED_TO_SECURITY_IDENTITY_AND_HISTORICAL_UNIVERSE_GATES_BEFORE_RETURNS"
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = build_audit(evidence)
    if args.input_csv:
        result["recomputed_panel"] = audit_csv(args.input_csv)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
