"""Phase 181: validate the preregistered IvyDB TradeFlow measurement protocol."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SUMMARY_PATH = Path(__file__).with_name("phase181_ivydb_tradeflow_measurement_protocol.json")
REQUIRED_HYPOTHESES = {"H1_information_continuation", "H2_hedging_or_temporary_price_pressure", "H3_participant_proxy_heterogeneity", "H4_flow_x_volatility_surface", "H5_execution_mechanism"}
REQUIRED_GATES = {
    "Raw sample across 2016, 2020, 2023 and 2026, including active and inactive/delisted underlyings",
    "Complete data dictionary, exact interval boundaries and cumulative-versus-incremental semantics",
    "First-publication/first-receipt timestamps and actual delivery latency",
    "Immutable corrections, cancellations, late-trade and revision-vintage policy",
    "Classifier methodology versions and historical backfill consistency",
    "Per-field participant/lot-size history, especially 2016 versus 2021",
    "Independent direction-label validation by trade condition, midpoint, venue and market regime",
    "Effective-dated security/contract identity and delisted coverage",
    "Pricing, internal-use license and derived-data rights",
}


def load_summary(path: Path = SUMMARY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_summary(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if summary.get("phase") != 181:
        errors.append("phase_mismatch")
    if summary.get("status") != "PREREGISTERED_NOT_DATA_ADMITTED":
        errors.append("status_mismatch")
    evidence = summary.get("source_evidence", {})
    if evidence.get("product_launch_date") != "2026-09-30" or evidence.get("vendor_advertised_history_start") != "2016-01":
        errors.append("product_timeline_mismatch")
    sample = evidence.get("methodology_example", {})
    if sample.get("midpoint_direction_assignment_share") != 0.999 or sample.get("interpretation", "").lower().find("not independently measured directional accuracy") < 0:
        errors.append("coverage_not_accuracy_guard_missing")
    semantics = summary.get("measurement_semantics", {})
    for key in ("beneficial_owner_identity", "open_close_status", "vendor_accuracy_independent_validation"):
        if semantics.get(key) is not False:
            errors.append("proxy_or_accuracy_scope_mislabelled:" + key)
    if semantics.get("institutional_1_nested_in_2") is not True or semantics.get("midpoint_is_subset_of_inside_nbbo") is not True:
        errors.append("overlap_guard_missing")
    if semantics.get("multi_leg_legs_signed_individually") is not True or semantics.get("unclassified_volume_retained") is not True:
        errors.append("microstructure_guard_missing")
    hypotheses = {x.get("id") for x in summary.get("hypotheses_not_tested", [])}
    if hypotheses != REQUIRED_HYPOTHESES:
        errors.append("hypothesis_set_mismatch")
    gates = {x.get("gate"): x.get("status") for x in summary.get("admission_gates", [])}
    if set(gates) != REQUIRED_GATES or any(status != "BLOCKED" for status in gates.values()):
        errors.append("admission_gate_set_or_status_mismatch")
    pit = summary.get("pit_rules", {})
    for key in ("event_time_is_not_availability_time",):
        if pit.get(key) is not True:
            errors.append("pit_rule_missing:" + key)
    if "does not prove" not in pit.get("historical_backfill", ""):
        errors.append("historical_backfill_vs_live_pit_distinction_missing")
    validation = summary.get("validation_protocol", {})
    if "F80_TOP20_PARTIAL50_BASELINE_C20" not in validation.get("baseline", ""):
        errors.append("frozen_baseline_missing")
    if validation.get("holdout") is None or "untouched" not in validation.get("holdout", ""):
        errors.append("holdout_lock_missing")
    if "no minimum or maximum" not in validation.get("holding_period", "").lower():
        errors.append("holding_period_constraint_added")
    decision = summary.get("decision", {})
    for key in ("feature_admitted", "backtest_authorized", "alpha_admitted", "holdout_used", "vendor_contact", "data_purchase", "production_changed"):
        if decision.get(key) is not False:
            errors.append("forbidden_admission_or_action:" + key)
    if decision.get("frozen_control") != "F80_TOP20_PARTIAL50_BASELINE_C20":
        errors.append("frozen_control_mismatch")
    return errors


def write_summary(output_dir: Path) -> Path:
    summary = load_summary()
    errors = validate_summary(summary)
    if errors:
        raise ValueError("phase181_validation_failed:" + ",".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / SUMMARY_PATH.name
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("phase181_output"))
    args = parser.parse_args()
    output = write_summary(args.output_dir)
    print(f"PHASE181_PROTOCOL_COMPLETE status=PREREGISTERED_NOT_DATA_ADMITTED output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
