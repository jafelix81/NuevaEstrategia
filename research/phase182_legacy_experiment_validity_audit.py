"""Phase 182: deterministic adjudication of legacy Smart Money experiments.

Metadata/code-validity audit only. No downloads, return recomputation, final-holdout
access, or production changes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT_INPUT = Path(__file__).with_name("phase182_legacy_experiment_validity_snapshot.json")


def audit(snapshot: dict) -> dict:
    finra = snapshot["sources"]["finra_20c"]
    cftc = snapshot["sources"]["cftc_23c"]
    form4 = snapshot["sources"]["sec_form4_21c"]
    finra_coverage = finra["files_available"] / finra["files_needed"]
    universe_coverage = finra["valid_universe"] / finra["configured_universe"]
    h5, h10, h20 = finra["horizons"]["5"], finra["horizons"]["10"], finra["horizons"]["20"]
    immature_5d_dates = sum(x["immature_5d_rows"] > 0 for x in cftc["maturity_audit"])
    immature_20d_dates = sum(x["immature_20d_rows"] > 0 for x in cftc["maturity_audit"])
    immature_5d_rows = sum(x["immature_5d_rows"] for x in cftc["maturity_audit"])
    immature_20d_rows = sum(x["immature_20d_rows"] for x in cftc["maturity_audit"])
    form4_ci = {
        horizon: values["bootstrap_ci_low"] <= 0 <= values["bootstrap_ci_high"]
        for horizon, values in form4["horizons"].items()
    }
    form4_residual_nonpositive = all(
        values["mean_residual_spearman"] <= 0 for values in form4["horizons"].values()
    )
    return {
        "phase": 182,
        "status": "NO_LEGACY_SMART_MONEY_SIGNAL_PROMOTED",
        "finra_20c": {
            "file_coverage": finra_coverage,
            "universe_coverage": universe_coverage,
            "pseudo_oos_dates": finra["pseudo_oos_test_dates"],
            "h5_mean_to_std": h5["mean_delta_replacement_minus_blocked"] / h5["std_delta"],
            "h5_median_negative": h5["median_delta"] < 0,
            "h5_positive_date_rate": h5["positive_dates"] / h5["n_dates"],
            "h10_mean_negative": h10["mean_delta_replacement_minus_blocked"] < 0,
            "h20_mean_negative": h20["mean_delta_replacement_minus_blocked"] < 0,
            "factor_selection_count": len(finra["selection_frequency"]),
            "decision": "NO_PROMOTION_WEAK_INCONSISTENT_AND_INCOMPLETE_FILE_COVERAGE"
        },
        "finra_20b": {
            "final_oos_dates": len(snapshot["sources"]["finra_20b"]["final_oos_dates"]),
            "costs_included": snapshot["sources"]["finra_20b"]["costs_included"],
            "bootstrap_ci_available": snapshot["sources"]["finra_20b"]["bootstrap_ci_available"],
            "holdout_consumed": snapshot["sources"]["finra_20b"]["holdout_consumed"],
            "decision": "EXPLORATORY_ONLY_NOT_CONFIRMATORY"
        },
        "cftc_23c": {
            "test_dates": len(cftc["test_dates"]),
            "immature_5d_test_dates": immature_5d_dates,
            "immature_5d_rows": immature_5d_rows,
            "immature_20d_test_dates": immature_20d_dates,
            "immature_20d_rows": immature_20d_rows,
            "training_embargo_present": cftc["training_embargo_present"],
            "decision": "QUARANTINED_LABEL_MATURITY_FILTER_MISSING"
        },
        "sec_form4_21c": {
            "all_bootstrap_intervals_cross_zero": all(form4_ci.values()),
            "bootstrap_intervals_cross_zero": form4_ci,
            "all_mean_residual_spearman_nonpositive": form4_residual_nonpositive,
            "decision": "KILLED_NO_ROBUST_INCREMENTAL_EDGE"
        },
        "holdout": {
            "status": snapshot["consumed_final_holdout"]["status"],
            "dates": snapshot["consumed_final_holdout"]["dates"],
            "phase182_used_final_holdout": snapshot["decision"]["phase182_used_final_holdout"]
        },
        "controls": {
            "f80_frozen": snapshot["decision"]["f80_frozen"],
            "production_changed": snapshot["decision"]["production_changed"],
            "vendor_contact": snapshot["decision"]["vendor_contact"],
            "data_purchase": snapshot["decision"]["data_purchase"]
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=Path("phase182_output"))
    args = parser.parse_args()
    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    result = audit(snapshot)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "phase182_legacy_experiment_validity_audit.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
