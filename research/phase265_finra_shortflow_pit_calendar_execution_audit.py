"""Phase 265: fail-closed PIT, calendar and execution audit for legacy FINRA short flow.

This module audits the existing Phase 20C implementation and supplies small,
deterministic contracts for session-based coverage, next-session execution,
label maturity and strict point-in-time admission. It does not download data,
calculate returns, or use any holdout.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

PHASE20C_RUN_ID = 40098425254
PHASE20C_JOB_ID = 120885427795
PHASE20C_ARTIFACT_ID = 12562171831
PHASE20C_ARTIFACT_SHA256 = "c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c"
PHASE20C_SCRIPT_BLOB_SHA = "6974d4b70a63c5e4b8dc460d6f90dfd652f16fa7"

def _as_date(value: str | date) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))

def _as_utc(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)

def session_coverage(
    expected_xnys_sessions: Iterable[str | date],
    observed_file_dates: Iterable[str | date],
) -> dict:
    """Measure file coverage only against an explicit authoritative session list."""
    expected_list = [_as_date(x) for x in expected_xnys_sessions]
    observed_list = [_as_date(x) for x in observed_file_dates]
    if len(set(expected_list)) != len(expected_list):
        raise ValueError("expected session list contains duplicates")
    if len(set(observed_list)) != len(observed_list):
        raise ValueError("observed file dates contain duplicates")
    expected = set(expected_list)
    observed = set(observed_list)
    matched = sorted(expected & observed)
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    rate = (len(matched) / len(expected)) if expected else None
    return {
        "expected_sessions": len(expected),
        "observed_expected_sessions": len(matched),
        "missing_expected_sessions": [x.isoformat() for x in missing],
        "unexpected_observed_dates": [x.isoformat() for x in unexpected],
        "coverage_rate": rate,
        "denominator_is_explicit_session_calendar": True,
    }

def next_xnys_session_after(
    trade_date: str | date,
    xnys_sessions: Iterable[str | date],
) -> str | None:
    """Return the first supplied XNYS session strictly after trade_date."""
    d = _as_date(trade_date)
    sessions = [_as_date(x) for x in xnys_sessions]
    if len(set(sessions)) != len(sessions):
        raise ValueError("session list contains duplicates")
    later = sorted(x for x in sessions if x > d)
    return later[0].isoformat() if later else None

def label_is_mature(label_end_session: str | date, test_entry_session: str | date) -> bool:
    """Strict embargo: a training label must end before the test entry session."""
    return _as_date(label_end_session) < _as_date(test_entry_session)

def strict_pit_gate(
    first_receipt_utc: str | datetime | None,
    entry_time_utc: str | datetime | None,
    raw_sha256: str | None,
    immutable_vintage_preserved: bool,
) -> dict:
    reasons: list[str] = []
    receipt = None
    entry = None
    if first_receipt_utc is None:
        reasons.append("MISSING_FIRST_RECEIPT_TIMESTAMP")
    else:
        try:
            receipt = _as_utc(first_receipt_utc)
        except (TypeError, ValueError):
            reasons.append("INVALID_FIRST_RECEIPT_TIMESTAMP")
    if entry_time_utc is None:
        reasons.append("MISSING_ENTRY_TIMESTAMP")
    else:
        try:
            entry = _as_utc(entry_time_utc)
        except (TypeError, ValueError):
            reasons.append("INVALID_ENTRY_TIMESTAMP")
    if not raw_sha256 or not re.fullmatch(r"[0-9a-fA-F]{64}", str(raw_sha256)):
        reasons.append("MISSING_OR_INVALID_RAW_SHA256")
    if immutable_vintage_preserved is not True:
        reasons.append("IMMUTABLE_VINTAGE_NOT_PRESERVED")
    if receipt is not None and entry is not None and receipt >= entry:
        reasons.append("RECEIPT_NOT_STRICTLY_BEFORE_ENTRY")
    return {"admitted": not reasons, "reasons": reasons}

def build_result() -> dict:
    files_needed = 2020
    files_available = 1382
    return {
        "phase": 265,
        "audit_date": "2026-11-10",
        "status": "PHASE20C_FINRA_SHORTFLOW_NON_PIT_DIAGNOSTIC_QUARANTINED",
        "source": {
            "run_id": PHASE20C_RUN_ID,
            "job_id": PHASE20C_JOB_ID,
            "artifact_id": PHASE20C_ARTIFACT_ID,
            "artifact_zip_sha256": PHASE20C_ARTIFACT_SHA256,
            "script_git_blob_sha": PHASE20C_SCRIPT_BLOB_SHA,
            "script_path": "Nueva_Estrategia_Fase20C_FINRA_WalkForward_OOS.py",
        },
        "sample": {
            "requested_calendar_dates": files_needed,
            "files_available": files_available,
            "calendar_date_success_ratio": round(files_available / files_needed, 6),
            "calendar_date_success_ratio_is_market_session_coverage": False,
            "expected_xnys_sessions": None,
            "xnys_session_coverage": None,
            "coverage_disposition": "NOT_MEASURED_REQUIRES_EXPLICIT_XNYS_CALENDAR",
            "valid_universe_names": 329,
            "configured_universe_names": 335,
            "name_availability_ratio": round(329 / 335, 6),
            "universe_is_representative_or_survivorship_free": False,
        },
        "walk_forward": {
            "all_training_signals": 24,
            "finra_eligible_training_signals": 20,
            "pseudo_oos_test_dates": 12,
            "final_holdout_signals_left_untouched_by_phase20c": 6,
            "selection_uses_prior_signal_dates_only": True,
            "chronological_selection": True,
            "label_maturity_revalidated_in_phase265": False,
            "strict_pit": False,
        },
        "timing_and_vintages": {
            "feature_uses_signal_date_finra_row": True,
            "entry_return_denominator_uses_same_signal_date_close": True,
            "download_audit_fields": ["Date", "Status"],
            "first_receipt_utc_recorded": False,
            "raw_sha256_per_file_recorded": False,
            "immutable_first_publication_and_revision_vintages": False,
            "same_day_close_availability_proven": False,
            "strict_pit_admitted": False,
            "safe_rule": "Use the first XNYS session strictly after verified first receipt; if only FINRA trade date is known, use the next XNYS session after that trade date.",
        },
        "economic_diagnostic": {
            "source": "research/smart_money/FINRA_SHORTFLOW_AUDIT_2026-10-24.md",
            "n_pseudo_oos_dates": 12,
            "horizons": {
                "5": {"mean_delta_pct": 0.141, "median_delta_pct": -0.049, "positive_dates": 5, "positive_rate": 0.416667},
                "10": {"mean_delta_pct": -1.686, "median_delta_pct": -1.837, "positive_dates": 3, "positive_rate": 0.25},
                "20": {"mean_delta_pct": -0.858, "median_delta_pct": -0.333, "positive_dates": 5, "positive_rate": 0.416667},
            },
            "selected_factor_counts": {
                "SHORT_RATIO_Z20": 6,
                "SHORT_EXEMPT_RATIO": 5,
                "SHORT_RATIO_PERSIST20": 1,
            },
            "interpretation": "Small diagnostic sample; factor selection migrates; H10 and H20 mean deltas are negative; no incremental edge demonstrated.",
        },
        "source_semantics": {
            "daily_short_sale_volume_is_short_interest": False,
            "consolidated_with_exchange_short_volume": False,
            "only_publicly_disseminated_trades": True,
            "offsetting_facilitation_purchase_may_be_absent": True,
        },
        "decision": {
            "phase20c_disposition": "QUARANTINE_AS_CHRONOLOGICAL_BUT_NOT_STRICT_PIT_DIAGNOSTIC",
            "calendar_coverage_claim": "RETRACT_1382_OF_2020_AS_MARKET_DAY_COVERAGE",
            "feature_admitted": False,
            "alpha_admitted": False,
            "retest_same_dates_authorized": False,
            "holdout_used": False,
            "legacy_holdout": "CONSUMED_NOT_PRISTINE",
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
        },
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="research/phase265_finra_shortflow_pit_calendar_execution_audit_result.json")
    args = parser.parse_args()
    result = build_result()
    rendered = json.dumps(result, indent=2) + "\n"
    Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")

if __name__ == "__main__":
    main()
