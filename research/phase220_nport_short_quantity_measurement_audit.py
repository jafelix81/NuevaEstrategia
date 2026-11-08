#!/usr/bin/env python3
"""Phase 220: N-PORT short-position quantity versus NAV exposure decomposition."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EVIDENCE = Path(__file__).with_name("phase220_nport_short_quantity_measurement_audit.json")


def quantity_change_pct(prior_balance: float, current_balance: float,
                        current_to_prior_basis_factor: float = 1.0) -> float:
    """Short-share quantity change, with current shares mapped to prior share basis."""
    if prior_balance >= 0 or current_balance >= 0:
        raise ValueError("explicit_negative_short_balances_required")
    if current_to_prior_basis_factor <= 0:
        raise ValueError("corporate_action_factor_must_be_positive")
    prior_q = abs(prior_balance)
    current_q = abs(current_balance) * current_to_prior_basis_factor
    if prior_q <= 0:
        raise ValueError("prior_short_quantity_must_be_positive")
    return 100.0 * (current_q / prior_q - 1.0)


def build_audit(e: dict) -> dict:
    if e.get("phase") != 220:
        raise ValueError("unexpected_phase")
    m = e["measurement"]
    if m["primary_feature"] != "delta_short_shares_pct":
        raise ValueError("primary_behavior_measure_must_be_quantity")
    if "not trade flow" not in m["interpretation"]:
        raise ValueError("quantity_change_mislabelled_as_trade_flow")
    if "explicit short rows in both periods" not in m["eligible_pair"]:
        raise ValueError("pair_completeness_rule_changed")
    if "otherwise exclude" not in m["corporate_actions"]:
        raise ValueError("corporate_action_gate_missing")
    if "no zero imputation" not in m["zero_or_missing_prior"]:
        raise ValueError("missingness_rule_changed")
    if e["supersedes"]["prior_primary_feature"] != "delta_short_pct_nav":
        raise ValueError("phase219_predecessor_not_preserved")
    if "exposure-state descriptor" not in e["supersedes"]["disposition"]:
        raise ValueError("nav_delta_misclassified_as_behavior")
    if e["point_in_time"]["report_date_is_knowledge_time"] is not False:
        raise ValueError("report_date_lookahead")
    if e["point_in_time"]["fixed_filing_lag"] is not False:
        raise ValueError("fixed_lag_forbidden")
    if e["point_in_time"]["amendments_update_state_only_after_own_acceptance"] is not True:
        raise ValueError("amendment_vintage_rule_changed")
    if e["economic_test"]["alpha_test_authorized"] is not False:
        raise ValueError("premature_alpha_authorization")
    c = e["controls"]
    for key in ("return_test_run", "alpha_test_run", "bootstrap_loo_run",
                "holdout_used", "production_changed", "universe_changed",
                "data_purchase", "vendor_contact", "sec_requests_sent"):
        if c[key] is not False:
            raise ValueError("control_violation:" + key)
    if c["f80_frozen"] is not True or c["legacy_holdout"] != "CONSUMED_NOT_PRISTINE":
        raise ValueError("frozen_control_or_holdout_changed")

    examples = e["synthetic_counterexamples"]
    for name, row in examples.items():
        if row["delta_short_shares_pct"] != quantity_change_pct(
            -row["prior_shares"], -row["current_shares"], 1.0
        ):
            raise ValueError("synthetic_quantity_example_mismatch:" + name)
    if examples["unchanged_shares_price_rises_20pct"]["delta_short_pct_nav_percentage_points"] <= 0:
        raise ValueError("price_revaluation_counterexample_missing")
    if examples["unchanged_shares_nav_falls"]["delta_short_pct_nav_percentage_points"] <= 0:
        raise ValueError("nav_denominator_counterexample_missing")

    return {
        "phase": 220,
        "status": e["status"],
        "primary_feature": m["primary_feature"],
        "nav_delta_role": "EXPOSURE_STATE_ONLY_NOT_BEHAVIOR",
        "synthetic_counterexamples_validated": len(examples),
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "decision": "WAIT_FOR_RAW_PIT_CORPORATE_ACTION_AND_SECURITY_IDENTITY_GATES"
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
        args.output.write_text(payload + "\\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
