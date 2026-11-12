#!/usr/bin/env python3
"""Phase 317: adjudicate N-PORT filing clocks, amendment lags and repeatability.

Offline only: consumes two immutable Phase 316 artifacts plus the Phase 310
purposive-control artifact. No SEC requests, market data, returns or alpha tests.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

SEC_FILER_MANUAL = (
    "https://www.sec.gov/files/edgar/filermanual/archive/efmvol2-v72.pdf"
)
SEC_RULE = "17 CFR 232.13"
AFTER_HOURS_CUTOFF = time(17, 30)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[int], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile_empty_input")
    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def classify_filing_clock(acceptance_datetime_et: str, filed_date: str) -> dict[str, Any]:
    accepted = datetime.strptime(acceptance_datetime_et, "%Y%m%d%H%M%S")
    filed = date.fromisoformat(filed_date)
    delta = (filed - accepted.date()).days
    after_cutoff = accepted.time() >= AFTER_HOURS_CUTOFF
    if delta < 0:
        classification = "INVALID_FILED_DATE_PRECEDES_ACCEPTANCE_DATE"
    elif delta == 0 and after_cutoff:
        classification = "SAME_FILED_DATE_ACCEPTED_AFTER_1730_START_TIME_UNRESOLVED"
    elif delta == 0:
        classification = "SAME_CALENDAR_DATE"
    elif after_cutoff:
        classification = "NEXT_FILED_DATE_AFTER_1730_CONSISTENT_WITH_SEC_RULE"
    else:
        classification = "UNEXPLAINED_DATE_SHIFT_BEFORE_1730"
    return {
        "acceptance_date": accepted.date().isoformat(),
        "acceptance_time_et": accepted.time().isoformat(),
        "filed_date": filed.isoformat(),
        "calendar_day_shift": delta,
        "acceptance_at_or_after_1730_et": after_cutoff,
        "classification": classification,
    }


def lag_summary(rows: list[dict[str, str]], form_type: str) -> dict[str, Any]:
    lags = []
    for row in rows:
        if row["form_type"] != form_type:
            continue
        report = date.fromisoformat(row["report_date"])
        filed = date.fromisoformat(row["master_index_filing_date"])
        lags.append((filed - report).days)
    if not lags:
        raise ValueError(f"no_lags_for_form:{form_type}")
    return {
        "form_type": form_type,
        "n": len(lags),
        "min_days": min(lags),
        "p25_days": round(percentile(lags, 0.25), 2),
        "median_days": statistics.median(lags),
        "p75_days": round(percentile(lags, 0.75), 2),
        "p90_days": round(percentile(lags, 0.90), 2),
        "max_days": max(lags),
        "at_least_90_days": sum(v >= 90 for v in lags),
        "at_least_180_days": sum(v >= 180 for v in lags),
        "at_least_365_days": sum(v >= 365 for v in lags),
        "at_least_730_days": sum(v >= 730 for v in lags),
        "interpretation": "report-date-to-filing-date lag; not amendment delay from its parent",
    }


def verify_artifact(root: Path) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    result_path = root / "phase316_nport_multifiler_expansion_result.json"
    candidates_path = root / "nport_expanded_sample_candidates.csv"
    filings_path = root / "nport_expanded_filing_reconciliation.csv"
    short_path = root / "nport_expanded_short_rows.csv"
    if not all(p.is_file() for p in (result_path, candidates_path, filings_path, short_path)):
        raise FileNotFoundError(f"phase316_artifact_incomplete:{root}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("phase") != 316 or result.get("status") != "PASS_MULTIREGISTRANT_STRATIFIED_RAW_RECONCILIATION":
        raise ValueError("phase316_result_not_pass")
    candidates = read_csv(candidates_path)
    filings = read_csv(filings_path)
    short_rows = read_csv(short_path)
    expected = result["coverage"]["sampled_accessions"]
    if len(candidates) != expected or len(filings) != expected:
        raise ValueError("phase316_filing_count_mismatch")
    if len({r["accession"] for r in candidates}) != expected:
        raise ValueError("phase316_candidate_accession_duplicate")
    if len({r["accession"] for r in filings}) != expected:
        raise ValueError("phase316_filing_accession_duplicate")
    raw_dir = root / "raw"
    raw_files = list(raw_dir.glob("*.txt"))
    if len(raw_files) != expected:
        raise ValueError("phase316_raw_file_count_mismatch")
    by_accession = {r["accession"]: r for r in filings}
    for accession, row in by_accession.items():
        raw_path = root / row["raw_file"]
        if not raw_path.is_file() or sha256_file(raw_path) != row["raw_sha256"]:
            raise ValueError(f"phase316_raw_hash_mismatch:{accession}")
        if row["header_filed_as_of_date"] != row["master_index_filing_date"].replace("-", ""):
            raise ValueError(f"phase316_filed_as_of_date_mismatch:{accession}")
        if row["header_accession"] != accession or row["header_form"] != row["form_type"]:
            raise ValueError(f"phase316_header_identity_mismatch:{accession}")
    return result, candidates, filings, short_rows


def compare_repeat(first: Path, second: Path) -> dict[str, Any]:
    a_result, a_candidates, a_filings, a_short = verify_artifact(first)
    b_result, b_candidates, b_filings, b_short = verify_artifact(second)
    a = {r["accession"]: r["raw_sha256"] for r in a_filings}
    b = {r["accession"]: r["raw_sha256"] for r in b_filings}
    common = set(a) & set(b)
    matches = sum(a[k] == b[k] for k in common)
    if set(a) != set(b) or matches != len(a):
        raise ValueError("phase316_repeat_raw_hashes_not_identical")
    for key in ("coverage", "reconciliation", "holdings"):
        if a_result[key] != b_result[key]:
            raise ValueError(f"phase316_repeat_summary_mismatch:{key}")
    if {r["accession"] for r in a_candidates} != {r["accession"] for r in b_candidates}:
        raise ValueError("phase316_repeat_candidate_set_mismatch")
    if len(a_short) != len(b_short):
        raise ValueError("phase316_repeat_short_row_count_mismatch")
    short_key = lambda r: (r.get("accession", ""), r.get("row_number", ""))
    if sorted(a_short, key=short_key) != sorted(b_short, key=short_key):
        raise ValueError("phase316_repeat_short_row_content_mismatch")
    return {
        "run_a": 43166221052,
        "artifact_a": 13919534524,
        "run_b": 43166231154,
        "artifact_b": 13920352803,
        "accessions_compared": len(common),
        "raw_sha256_identical": matches,
        "raw_sha256_mismatches": len(common) - matches,
        "candidate_accession_sets_identical": True,
        "coverage_summary_identical": True,
        "reconciliation_summary_identical": True,
        "holdings_summary_identical": True,
        "short_row_count_identical": True,
        "short_row_content_identical": True,
    }


def analyze(first: Path, second: Path, phase310_dir: Path, output_dir: Path) -> dict[str, Any]:
    result316, candidates, filings, short_rows = verify_artifact(first)
    repeat = compare_repeat(first, second)
    phase310_path = phase310_dir / "phase310_output" / "phase310_nport_raw_vintage_validation.json"
    if not phase310_path.is_file():
        raise FileNotFoundError("phase310_control_artifact_incomplete")
    phase310 = json.loads(phase310_path.read_text(encoding="utf-8"))
    controls = {row["accession"] for row in phase310.get("accessions", [])}
    sample_accessions = {row["accession"] for row in candidates}
    overlap = sorted(controls & sample_accessions)
    if len(controls) != 5:
        raise ValueError("phase310_purposive_control_count_unexpected")
    if overlap:
        raise ValueError("phase316_sample_overlaps_phase310_purposive_controls")

    clock_rows = []
    mismatch_rows = []
    for row in filings:
        clock = classify_filing_clock(row["acceptance_datetime_et"], row["master_index_filing_date"])
        item = {
            "accession": row["accession"],
            "quarter": row["quarter"],
            "registrant_cik": row["registrant_cik"],
            "form_type": row["form_type"],
            "company_name": row["company_name"],
            "report_date": row["report_date"],
            "master_index_filing_date": row["master_index_filing_date"],
            "acceptance_datetime_et": row["acceptance_datetime_et"],
            **clock,
        }
        clock_rows.append(item)
        if clock["calendar_day_shift"] != 0:
            mismatch_rows.append(item)
    if any(r["classification"] == "UNEXPLAINED_DATE_SHIFT_BEFORE_1730" for r in clock_rows):
        raise ValueError("unexplained_acceptance_filed_date_mismatch")
    if any(r["classification"] == "INVALID_FILED_DATE_PRECEDES_ACCEPTANCE_DATE" for r in clock_rows):
        raise ValueError("filed_date_precedes_acceptance_date")
    if any(not r["acceptance_at_or_after_1730_et"] for r in mismatch_rows):
        raise ValueError("date_mismatch_not_after_1730")
    after_cutoff = [r for r in clock_rows if r["acceptance_at_or_after_1730_et"]]
    same_date_after_cutoff = [r for r in after_cutoff if r["calendar_day_shift"] == 0]
    mismatch_shifts = Counter(str(r["calendar_day_shift"]) for r in mismatch_rows)

    lag_p = lag_summary(filings, "NPORT-P")
    lag_pa = lag_summary(filings, "NPORT-P/A")
    forms = Counter(r["form_type"] for r in filings)
    strata = Counter((r["quarter"], r["form_type"]) for r in candidates)
    if len(candidates) != 280 or forms != Counter({"NPORT-P": 140, "NPORT-P/A": 140}):
        raise ValueError("phase316_expected_sample_design_changed")
    if len(strata) != 56 or any(count != 5 for count in strata.values()):
        raise ValueError("phase316_quarter_form_quota_failed")
    if len({r["cik"] for r in candidates}) != 212:
        raise ValueError("phase316_registrant_count_changed")

    short_accessions = Counter(r["accession"] for r in short_rows)
    short_cusips = {r["cusip"] for r in short_rows if r.get("cusip", "").strip()}
    short_isins = {r["isin"] for r in short_rows if r.get("isin", "").strip()}
    short_tickers = {r["ticker"] for r in short_rows if r.get("ticker", "").strip()}
    cusip_present = sum(bool(r.get("cusip", "").strip()) for r in short_rows)
    isin_present = sum(bool(r.get("isin", "").strip()) for r in short_rows)
    ticker_present = sum(bool(r.get("ticker", "").strip()) for r in short_rows)
    short_by_accession = []
    for accession, count in sorted(short_accessions.items()):
        filing = next(r for r in filings if r["accession"] == accession)
        short_by_accession.append({
            "accession": accession,
            "registrant_cik": filing["registrant_cik"],
            "company_name": filing["company_name"],
            "report_date": filing["report_date"],
            "filing_date": filing["master_index_filing_date"],
            "rows": count,
        })
    if len(short_rows) != 194 or len(short_accessions) != 2:
        raise ValueError("phase316_short_row_result_changed")
    if len(short_cusips) != 173 or len(short_isins) != 174 or ticker_present != 0:
        raise ValueError("phase316_short_identifier_coverage_changed")

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "nport_clock_adjudication_rows.csv", clock_rows, list(clock_rows[0].keys()))
    write_csv(output_dir / "nport_acceptance_filed_date_mismatches.csv", mismatch_rows, list(mismatch_rows[0].keys()))
    result = {
        "phase": 317,
        "status": "PASS_NPORT_FILING_CLOCK_AND_REPEATABILITY_ADJUDICATION",
        "source_artifacts": {
            "phase316_run_a": 43166221052,
            "phase316_artifact_a": 13919534524,
            "phase316_run_b": 43166231154,
            "phase316_artifact_b": 13920352803,
            "phase310_run": 43154326395,
            "phase310_artifact": 13915126393,
        },
        "sample": {
            "accessions": len(candidates),
            "quarters": len({r["quarter"] for r in candidates}),
            "quarter_form_strata": len(strata),
            "per_stratum": 5,
            "nport_p": forms["NPORT-P"],
            "nport_p_a": forms["NPORT-P/A"],
            "distinct_registrant_ciks": len({r["cik"] for r in candidates}),
            "phase311_prior_accessions_excluded": result316["coverage"]["prior_phase311_accessions_excluded"],
            "phase310_purposive_controls": len(controls),
            "phase310_control_overlap": len(overlap),
            "probability_sample": False,
        },
        "repeatability": repeat,
        "filing_clock": {
            "filed_as_of_date_equals_master_index_date": len(filings),
            "acceptance_calendar_date_matches_filed_date": len(filings) - len(mismatch_rows),
            "acceptance_calendar_date_precedes_filed_date": len(mismatch_rows),
            "acceptance_at_or_after_1730_et": len(after_cutoff),
            "after_1730_same_filed_date_unresolved": len(same_date_after_cutoff),
            "after_1730_next_filed_date_consistent": len(mismatch_rows),
            "calendar_day_shift_distribution": dict(sorted(mismatch_shifts.items())),
            "date_mismatch_accessions": [r["accession"] for r in mismatch_rows],
            "first_public_receipt_time_verified": False,
            "acceptance_datetime_is_first_public_time": False,
            "sec_rule": SEC_RULE,
            "sec_filer_manual_version": "Version 72, December 2024",
            "sec_filer_manual_url": SEC_FILER_MANUAL,
            "nport_in_10pm_exception_list": False,
            "conservative_backtest_availability_rule": (
                "Use the official SEC FILED AS OF DATE / master-index filing date as the date-level "
                "public filing anchor, then permit strategy use only from the first full XNYS session "
                "strictly after that date. Do not backdate to REPORT_DATE or use ACCEPTANCE-DATETIME "
                "alone as the first-public clock."
            ),
        },
        "report_to_filing_lag_days": {
            "NPORT-P": lag_p,
            "NPORT-P/A": lag_pa,
        },
        "short_holdings": {
            "sign_concordant_rows": len(short_rows),
            "filings_with_short_rows": len(short_accessions),
            "filings": short_by_accession,
            "unique_cusips": len(short_cusips),
            "unique_isins": len(short_isins),
            "unique_tickers": len(short_tickers),
            "cusip_present_rows": cusip_present,
            "isin_present_rows": isin_present,
            "ticker_present_rows": ticker_present,
            "cusip_check_digit_valid_rows": result316["holdings"]["identifier_metrics"]["cusip_check_digit_valid"],
            "isin_check_digit_valid_rows": result316["holdings"]["identifier_metrics"]["isin_check_digit_valid"],
        },
        "legacy_nport_phase27o_disposition": {
            "status": "QUARANTINED_IMPLEMENTATION_DEFECT_NOT_NEGATIVE_ALPHA",
            "reason": "Legacy Phase 27O read UNITS from the SEC flattened FUND_REPORTED_HOLDING table; the official field is UNIT (singular). Phase 247 confirmed this schema defect. Its zero-share/zero-rank output is not an economic null result.",
            "phase247_report": "research/PHASE247_NPORT_FLATTENED_UNIT_FIELD_AND_PIT_DESIGN_AUDIT_2026-11-09.md",
            "phase27o_output_admitted": False,
        },
        "controls": {
            "raw_bytes_repeated_identically": True,
            "raw_hashes_identical_count": repeat["raw_sha256_identical"],
            "nport_p_and_p_a_separate": True,
            "amendments_are_new_trades": False,
            "report_date_is_knowledge_date": False,
            "acceptance_datetime_is_first_public_time": False,
            "effective_dated_security_master_complete": False,
            "f80_universe_coverage_measured": False,
            "returns_test": False,
            "alpha_test": False,
            "bootstrap": False,
            "loo": False,
            "chronological_oos": False,
            "holdout_used": False,
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
            "parameters_changed": False,
            "vendor_contact": False,
            "data_purchase": False,
            "email_sent": False,
        },
        "decision": (
            "N-PORT raw filing identity and parser coverage are reproducible across 280 multi-registrant "
            "accessions, but the short-position sample has no ticker values and requires an effective-dated "
            "CUSIP/ISIN security master. The legal filed date, not acceptance calendar date or report date, "
            "is the conservative public-date anchor; backtests should wait until the first full XNYS session "
            "after that date. Amendments must correct prior state rather than create fresh flow events."
        ),
    }
    (output_dir / "phase317_nport_filing_clock_adjudication_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = [
        "# Phase 317 — N-PORT filing-clock and amendment-lag adjudication",
        "",
        "**Status:** PASS — offline adjudication of the repeated Phase 316 raw sample.",
        "",
        "## Sample and repeatability",
        "",
        f"- {len(candidates)} accessions across {len({r['quarter'] for r in candidates})} quarters and {len(strata)} quarter/form strata; five distinct registrants per stratum.",
        f"- {len({r['cik'] for r in candidates})} distinct registrant CIKs; 140 NPORT-P and 140 NPORT-P/A filings.",
        f"- Phase 316 independent repeat: {repeat['raw_sha256_identical']}/{repeat['accessions_compared']} raw accession SHA-256 hashes identical.",
        f"- Phase 310 purposive positive controls: {len(controls)}; overlap with the Phase 316 expansion sample: {len(overlap)}.",
        "- This is a deterministic hash-ranked QA sample, not a probability sample or prevalence estimate.",
        "",
        "## Filing clock: acceptance time is not the public clock",
        "",
        f"- FILED AS OF DATE equals the SEC master-index filing date in {len(filings)}/{len(filings)} filings.",
        f"- Acceptance calendar date equals filed date in {len(filings)-len(mismatch_rows)}/{len(filings)}.",
        f"- {len(mismatch_rows)} filings have acceptance date before the official filed date; all {len(mismatch_rows)} have acceptance time at or after 17:30 ET. Calendar-day shifts: {dict(sorted(mismatch_shifts.items()))}.",
        f"- {len(same_date_after_cutoff)} additional filing was accepted after 17:30 ET but retains the same filed date; its transmission-start/public-dissemination time is unresolved.",
        "- The SEC's December 2024 EDGAR Filer Manual says ordinary filings received after 5:30 p.m. ET normally receive the next business day's filing date and are not disseminated until that next business day. Its enumerated 10 p.m. exceptions include Forms 3/4/5, 144 and Schedules 13D/G; N-PORT is not listed.",
        f"- Source: [SEC EDGAR Filer Manual, Version 72, December 2024]({SEC_FILER_MANUAL}), section 3.2, filing-date guidance; see also {SEC_RULE}.",
        "- The acceptance timestamp is not a verified first-public-receipt timestamp. Use the official FILED AS OF DATE / master-index filing date as the date-level public anchor, then allow use only from the first full XNYS session strictly after that date. Do not use REPORT_DATE or ACCEPTANCE-DATETIME alone as the knowledge clock.",
        "",
        "## Report-to-filing lag",
        "",
        f"- NPORT-P: n={lag_p['n']}, median {lag_p['median_days']} days, range {lag_p['min_days']}–{lag_p['max_days']}.",
        f"- NPORT-P/A: n={lag_pa['n']}, median {lag_pa['median_days']} days, range {lag_pa['min_days']}–{lag_pa['max_days']}; {lag_pa['at_least_90_days']} of 140 at least 90 days, {lag_pa['at_least_180_days']} at least 180 days, {lag_pa['at_least_365_days']} at least 365 days, and {lag_pa['at_least_730_days']} at least 730 days.",
        "- These are report-date-to-filing-date lags, not the elapsed time from the original filing to an amendment. Amendments remain state corrections, not new trading events.",
        "",
        "## Short-holding coverage",
        "",
        f"- {len(short_rows)} sign-concordant short rows in {len(short_accessions)} NPORT-P filings.",
        f"- {len(short_cusips)} unique CUSIPs and {len(short_isins)} unique ISINs; zero ticker values.",
        f"- CUSIP present on {cusip_present}/194 rows; ISIN present on {isin_present}/194; ticker present on {ticker_present}/194.",
        "- Both filings are new registrants in this expansion sample, not the Phase 310 purposive controls. These rows are reported holdings snapshots, not trades or short-sale executions.",
        "",
        "## Legacy Phase 27O result",
        "",
        "- The old zero-share/zero-rank output is quarantined as an implementation defect, not a negative alpha result: the legacy code read UNITS while the SEC flattened schema field is UNIT. Phase 247 already confirmed this. Do not use Phase 27O's zero ranking as evidence against N-PORT.",
        "",
        "## Decision",
        "",
        "- Raw identity and parser coverage are reproducible, but the 194 short rows have no ticker values and require an effective-dated CUSIP/ISIN crosswalk.",
        "- OpenFIGI's current mapping snapshot is not a standalone historical PIT security master; the prior audit left 19.7% of sampled CUSIPs unmatched and supplied no effective dates.",
        "- Databento remains a potential commercial security-master route, but no purchase or vendor contact is authorized or performed.",
        "- No return, alpha, bootstrap, LOO, chronological OOS or holdout test was run. F80 and production remain frozen.",
        "",
        "## Outputs",
        "",
        "- phase317_nport_filing_clock_adjudication_result.json",
        "- nport_clock_adjudication_rows.csv",
        "- nport_acceptance_filed_date_mismatches.csv",
        "",
    ]
    (output_dir / "PHASE317_NPORT_FILING_CLOCK_ADJUDICATION_2026-11-12.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase316-a", type=Path, default=Path("phase316_a"))
    parser.add_argument("--phase316-b", type=Path, default=Path("phase316_b"))
    parser.add_argument("--phase310", type=Path, default=Path("phase310_input"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase317_output"))
    args = parser.parse_args()
    result = analyze(args.phase316_a, args.phase316_b, args.phase310, args.output_dir)
    print(json.dumps({
        "phase": 317,
        "status": result["status"],
        "sample": result["sample"],
        "filing_clock": result["filing_clock"],
        "report_to_filing_lag_days": result["report_to_filing_lag_days"],
        "short_holdings": result["short_holdings"],
        "repeatability": result["repeatability"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
