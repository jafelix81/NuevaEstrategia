"""Phase 180: validate the static IvyDB TradeFlow documentation-feasibility audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SUMMARY_PATH = Path(__file__).with_name("phase180_ivydb_tradeflow_documentation_feasibility.json")
EXPECTED_TABLES = {"Signed_Volume", "Trade_Conditions", "Market_Structure", "Signed_Exchange"}
EXPECTED_INTERVALS = {"5-minute", "30-minute", "end-of-day"}
EXPECTED_BLOCKED_GATES = {
    "Per-year, per-underlying, per-contract and inactive/delisted coverage",
    "Exact 5-minute/30-minute interval boundaries and cumulative-versus-incremental semantics",
    "First-publication and first-receipt timestamps/latency",
    "Late trades, cancellations, corrections and revision vintages",
    "Historical methodology version and uniform backfill of new classifier",
    "Lot-size and participant-proxy field history (2016 versus 2021)",
    "Raw sample and full data dictionary",
    "Price, internal-use license and derived-data rights",
    "TradeFlow versus IvyDB US Intraday timestamp alignment for delta/IV joins",
}


def load_summary(path: Path = SUMMARY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_summary(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if summary.get("phase") != 180:
        errors.append("phase_mismatch")
    if summary.get("status") != "CONDITIONAL_CANDIDATE_NOT_FEATURE_ADMITTED":
        errors.append("status_mismatch")
    product = summary.get("product", {})
    if product.get("launch_date") != "2026-09-30" or product.get("advertised_history_start") != "2016-01":
        errors.append("product_history_or_launch_mismatch")
    if set(product.get("intervals", [])) != EXPECTED_INTERVALS:
        errors.append("interval_set_mismatch")
    if set(product.get("tables", [])) != EXPECTED_TABLES:
        errors.append("table_set_mismatch")
    classifier = summary.get("classifier", {})
    if len(classifier.get("stages", [])) != 5 or classifier.get("unresolved_volume_retained") is not True:
        errors.append("classifier_semantics_mismatch")
    proxies = summary.get("participant_proxies", {})
    if proxies.get("retail_1_2_3_mutually_exclusive") is not True:
        errors.append("retail_bucket_overlap_rule_missing")
    if proxies.get("institutional_1_is_subset_of_institutional_2") is not True or proxies.get("institutional_1_and_2_additive") is not False:
        errors.append("institutional_bucket_nesting_rule_missing")
    if proxies.get("institutional_proxy_is_total_institutional_participation") is not False:
        errors.append("institutional_proxy_scope_mislabelled")
    micro = summary.get("microstructure_semantics", {})
    if micro.get("midpoint_is_subset_of_inside_NBBO") is not True:
        errors.append("midpoint_double_counting_guard_missing")
    if micro.get("multi_leg_legs_signed_individually") is not True:
        errors.append("multi_leg_semantics_missing")
    coverage = summary.get("historical_field_coverage", {})
    if coverage.get("legacy_signed_volume_lot_size_fields_start") != "2021" or coverage.get("tradeflow_lot_size_and_participant_proxy_backfill_start") != "UNRESOLVED":
        errors.append("lot_size_backfill_conflict_not_preserved")
    gates = {g.get("gate"): g.get("status") for g in summary.get("data_gates", [])}
    for gate in EXPECTED_BLOCKED_GATES:
        if not str(gates.get(gate, "")).startswith("BLOCKED"):
            errors.append("required_gate_not_blocked:" + gate)
    intraday = summary.get("complementary_data", {}).get("ivydb_us_intraday", {})
    if intraday.get("advertised_history_start") != "2018-01" or intraday.get("snapshots_et") != ["10:00", "14:00", "15:45"]:
        errors.append("intraday_greek_join_timing_mismatch")
    decision = summary.get("decision", {})
    for key in ("feature_admitted", "alpha_admitted", "backtest_authorized", "holdout_used", "data_purchase", "vendor_contact", "raw_data_request", "production_changed"):
        if decision.get(key) is not False:
            errors.append("forbidden_action_or_admission:" + key)
    if decision.get("frozen_control") != "F80_TOP20_PARTIAL50_BASELINE_C20":
        errors.append("frozen_control_mismatch")
    return errors


def write_summary(output_dir: Path) -> Path:
    summary = load_summary()
    errors = validate_summary(summary)
    if errors:
        raise ValueError("phase180_validation_failed:" + ",".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / SUMMARY_PATH.name
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("phase180_output"))
    args = parser.parse_args()
    output = write_summary(args.output_dir)
    print(f"PHASE180_DOC_AUDIT_COMPLETE status=CONDITIONAL_CANDIDATE_NOT_FEATURE_ADMITTED output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
