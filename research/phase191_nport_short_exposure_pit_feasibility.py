#!/usr/bin/env python3
"""Phase 191: SEC N-PORT registered-fund short-exposure PIT feasibility gate.

Documentation/evidence audit only. It does not download SEC archives, parse
short-position rows, retrieve returns, or run an alpha test.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

EVIDENCE_PATH = Path(__file__).with_name("phase191_nport_short_exposure_pit_feasibility.json")


def load_evidence(path: Path = EVIDENCE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    ev = evidence if evidence is not None else load_evidence()
    if ev.get("phase") != 191:
        raise ValueError("Unexpected Phase 191 evidence identity")
    coverage, schema = ev["coverage"], ev["bulk_dataset_schema"]
    short, pit = ev["short_position_semantics"], ev["pit"]
    identity, gates, controls = ev["identity_and_universe"], ev["admission_gates"], ev["controls"]

    if coverage["dataset_start"] != "2019-10-01" or coverage["dataset_end"] != "2026-09-30":
        raise ValueError("Unexpected SEC N-PORT data-set coverage interval")
    if int(coverage["quarterly_archive_count"]) != 28:
        raise ValueError("Unexpected number of quarterly N-PORT archives")
    if not all(coverage[k] for k in ("publicly_disseminated_filings_only", "as_filed", "includes_amendments")):
        raise ValueError("N-PORT public/as-filed/amendment scope must remain explicit")
    if schema["submission_table_has_acceptance_timestamp"]:
        raise ValueError("Bulk SUBMISSION table must not be treated as carrying acceptance time")
    if not schema["derivative_positions_have_separate_item_c11_tables"]:
        raise ValueError("Derivative and non-derivative payoff semantics must remain separate")
    if pit["report_date_is_knowledge_date"]:
        raise ValueError("Report date cannot be treated as public knowledge date")
    if identity["historical_security_crosswalk_admitted"] or identity["broad_pit_equity_universe_admitted"]:
        raise ValueError("Phase 191 cannot admit an unverified historical universe")
    if controls["return_test_run"] or controls["alpha_test_run"] or controls["holdout_used"] or controls["production_changed"]:
        raise ValueError("Phase 191 must remain a source-feasibility audit")
    if not controls["f80_frozen"]:
        raise ValueError("Frozen F80 control was changed")

    total_mb = round(float(coverage["archive_total_mb"]), 2)
    return {
        "phase": 191, "audit_as_of": ev["audit_as_of"], "source": ev["source"],
        "status": ev["status"], "classification": ev["classification"],
        "coverage": {
            "start": coverage["dataset_start"], "end": coverage["dataset_end"],
            "quarterly_archives": int(coverage["quarterly_archive_count"]),
            "compressed_archive_total_gb_decimal": round(total_mb / 1000.0, 5),
            "publication_frequency": coverage["publication_frequency"],
            "as_filed": coverage["as_filed"], "includes_amendments": coverage["includes_amendments"],
            "publicly_disseminated_filings_only": coverage["publicly_disseminated_filings_only"]
        },
        "short_position_gate": {
            "current_non_derivative_field": "PAYOFF_PROFILE",
            "short_equity_sample": "VERIFIED" if short["sample_short_equity_row_verified"] else "NOT_VERIFIED",
            "derivatives_in_first_hypothesis": short["derivatives_in_first_hypothesis"],
            "direct_short_scope": short["first_hypothesis_scope"]
        },
        "pit_gate": {
            "bulk_submission_table_has_acceptance_timestamp": schema["submission_table_has_acceptance_timestamp"],
            "first_public_receipt_capture_verified": pit["first_public_receipt_capture_verified"],
            "report_date_is_knowledge_date": pit["report_date_is_knowledge_date"],
            "amendments_append_only": True, "amendment_rule": pit["amendment_rule"],
            "knowledge_rule": pit["conservative_knowledge_rule"]
        },
        "identity_gate": {
            "series_id_portfolio_unit": identity["series_id_is_portfolio_unit"],
            "historical_security_crosswalk_admitted": identity["historical_security_crosswalk_admitted"],
            "historical_delisted_coverage_proven": identity["historical_delisted_coverage_proven"],
            "broad_pit_equity_universe_admitted": identity["broad_pit_equity_universe_admitted"]
        },
        "admission_gates": gates, "controls": controls, "decision": ev["decision"]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase191_output/phase191_nport_short_exposure_audit.json"))
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": result["phase"], "status": result["status"],
        "history": f'{result["coverage"]["start"]} to {result["coverage"]["end"]}',
        "quarterly_archives": result["coverage"]["quarterly_archives"],
        "compressed_archive_total_gb_decimal": result["coverage"]["compressed_archive_total_gb_decimal"],
        "short_equity_sample": result["short_position_gate"]["short_equity_sample"],
        "broad_pit_universe_admitted": result["identity_gate"]["broad_pit_equity_universe_admitted"],
        "alpha_test_authorized": result["admission_gates"]["alpha_test"] == "PASS",
        "f80_frozen": result["controls"]["f80_frozen"]
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
