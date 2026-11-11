#!/usr/bin/env python3
"""Phase 221: conservative N-PORT missing-row / Part-D semantics auditor."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

EVIDENCE = Path(__file__).with_name("phase221_nport_absence_semantics_audit.json")


def _unknown(reason: str) -> dict:
    return {"status": "UNKNOWN", "short_shares": None, "reason": reason}


def classify_direct_short_state(*, prior_public_part_c: bool,
                                current_period_public: bool,
                                current_filing_complete: bool,
                                same_series: bool,
                                same_security: bool,
                                corporate_action_clear: bool,
                                current_vintage_as_of_signal: bool,
                                part_d_ineligible_due_prior_public: bool,
                                current_part_c_rows):
    """Classify exact-instrument direct physical common-equity short state.

    current_part_c_rows=None means the parse/search is incomplete.
    current_part_c_rows=[] means a completed exact-security Part-C search found no row.
    """
    if not current_period_public:
        return _unknown("current_fiscal_period_not_public")
    if not current_vintage_as_of_signal:
        return _unknown("selected_vintage_not_yet_knowable")
    if not current_filing_complete:
        return _unknown("current_filing_or_part_c_parse_incomplete")
    if not same_series:
        return _unknown("fund_series_identity_not_exact")
    if not same_security:
        return _unknown("security_identity_not_exact")
    if not corporate_action_clear:
        return _unknown("corporate_action_or_listing_identity_unresolved")
    if current_part_c_rows is None:
        return _unknown("part_c_parse_missing_not_empty")
    if part_d_ineligible_due_prior_public and not prior_public_part_c:
        return _unknown("part_d_exclusion_claim_lacks_prior_public_part_c_row")

    short_quantities = []
    for row in current_part_c_rows:
        profile = str(row.get("payoff_profile", "")).strip().lower()
        unit = row.get("unit")
        asset_cat = row.get("asset_cat")
        issuer_cat = row.get("issuer_cat")
        balance = row.get("balance")
        try:
            balance = float(balance)
        except (TypeError, ValueError):
            return _unknown("non_numeric_balance")
        if not math.isfinite(balance):
            return _unknown("non_finite_balance")

        # Structured SEC fields carry the instrument classification.
        # ISSUER_TITLE is descriptive and need not literally contain "Common Stock".
        common_equity = unit == "NS" and asset_cat == "EC" and issuer_cat == "CORP"
        if not common_equity:
            return _unknown("row_not_verified_as_direct_common_equity")
        if profile == "short":
            if balance >= 0:
                return _unknown("short_profile_balance_not_negative")
            short_quantities.append(abs(balance))
        elif profile == "long":
            if balance <= 0:
                return _unknown("long_profile_balance_not_positive")
        else:
            return _unknown("payoff_profile_missing_or_not_long_short")

    if short_quantities:
        return {
            "status": "OBSERVED_SHORT_POSITION",
            "short_shares": sum(short_quantities),
            "reason": "valid_explicit_short_common_equity_rows_in_part_c"
        }
    if current_part_c_rows:
        return {
            "status": "OBSERVED_ZERO_DIRECT_SHORT_IN_PART_C",
            "short_shares": 0.0,
            "reason": "complete_exact_security_part_c_rows_contain_no_short_payoff"
        }
    if prior_public_part_c and part_d_ineligible_due_prior_public:
        return {
            "status": "CONDITIONAL_ZERO_BY_PART_D_EXCLUSION",
            "short_shares": 0.0,
            "reason": "prior_public_part_c_disclosure_blocks_part_d_omission_subject_to_legal_and_identity_gates"
        }
    return _unknown("absence_may_be_part_d_or_security_never_publicly_disclosed")


def build_audit(e: dict) -> dict:
    if e.get("phase") != 221:
        raise ValueError("unexpected_phase")
    if e["prior_phase"] != 220:
        raise ValueError("phase220_measurement_predecessor_missing")
    rb = e["regulatory_basis"]
    if rb["part_d"]["aggregate_cap_pct_total_assets"] != 5:
        raise ValueError("part_d_aggregate_cap_changed")
    if rb["part_d"]["public_information"] is not False:
        raise ValueError("part_d_must_remain_nonpublic")
    if rb["2026_proposal"]["status_as_of_audit"] != "PROPOSED_NOT_FINAL":
        raise ValueError("2026_proposal_misclassified")
    if e["interpretation"]["default_absence"] != "UNKNOWN_NOT_ZERO":
        raise ValueError("default_absence_rule_relaxed")
    if e["interpretation"]["legal_reading_confidence"] != "CONDITIONAL_CONSERVATIVE":
        raise ValueError("conditional_legal_reading_overstated")

    cases = e["synthetic_cases"]
    if len(cases) != 13:
        raise ValueError("synthetic_case_count_changed")
    for case in cases:
        got = classify_direct_short_state(**case["inputs"])
        if got["status"] != case["expected"]:
            raise ValueError("synthetic_case_failed:" + case["name"] + ":" + got["status"])
        if "expected_short_shares" in case and got["short_shares"] != case["expected_short_shares"]:
            raise ValueError("synthetic_quantity_failed:" + case["name"])

    c = e["controls"]
    for key in ("raw_filings_downloaded", "raw_hashes_verified", "alpha_test_authorized",
                "return_test_run", "bootstrap_loo_run", "holdout_used",
                "production_changed", "universe_changed", "data_purchase",
                "vendor_contact", "sec_requests_sent"):
        if c[key] is not False:
            raise ValueError("control_violation:" + key)
    if c["f80_frozen"] is not True or c["legacy_holdout"] != "CONSUMED_NOT_PRISTINE":
        raise ValueError("frozen_baseline_or_holdout_changed")

    return {
        "phase": 221,
        "status": e["status"],
        "synthetic_cases_validated": len(cases),
        "conditional_zero_rule": "PRIOR_PUBLIC_PART_C_ONLY_ALL_GATES_REQUIRED",
        "default_absence": "UNKNOWN_NOT_ZERO",
        "alpha_test_authorized": False,
        "raw_filings_downloaded": False,
        "holdout_used": False,
        "f80_frozen": True,
        "decision": "WAIT_FOR_HASH_VERIFIED_RAW_FILINGS_SERIES_SECURITY_IDENTITY_AND_PIT_PANEL"
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=EVIDENCE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_audit(json.loads(args.input.read_text(encoding="utf-8")))
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
