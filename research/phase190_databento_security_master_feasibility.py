#!/usr/bin/env python3
"""Phase 190: Databento PIT security-master feasibility gate.

Documentation-only. This script does not create an account, use an API key,
request data, contact a vendor, accept terms, spend credits, or run returns.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EVIDENCE_PATH = Path(__file__).with_name("phase190_databento_security_master_feasibility.json")


def load_evidence(path: Path = EVIDENCE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cost_scenario(symbols: int, included: int, low_rate: float, high_rate: float) -> dict[str, Any]:
    extra = max(0, symbols - included)
    return {
        "requested_symbols": symbols,
        "included_symbols": included,
        "extra_symbols": extra,
        "low_extra_usd_per_month": round(extra * low_rate, 2),
        "high_extra_usd_per_month": round(extra * high_rate, 2),
        "base_plan_excluded": True,
        "vendor_quote": False,
    }


def build_audit(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    ev = evidence if evidence is not None else load_evidence()
    if ev.get("phase") != 190 or ev.get("source") != "Databento Security Master":
        raise ValueError("Unexpected Phase 190 evidence identity")

    history = ev["history"]
    pit = ev["point_in_time"]
    pricing = ev["pricing"]
    controls = ev["controls"]

    required_time_fields = {"ts_record", "ts_effective", "ts_created"}
    if not required_time_fields.issubset(pit):
        raise ValueError("Missing required PIT timestamp semantics")
    if pit["get_range_supported_index"] != ["ts_effective", "ts_record"]:
        raise ValueError("Unexpected get_range time-axis contract")
    if history["start_date"] != "2005-01-01":
        raise ValueError("Unexpected documented history start")
    if not history["update_frequency_reconciled"]:
        cadence_gate = "UNRESOLVED_CONFLICT"
    else:
        cadence_gate = "DOCUMENTED"

    included = int(pricing["included_symbols_claimed"])
    low = float(pricing["sample_section_extra_usd_per_symbol_month"])
    high = float(pricing["faq_extra_usd_per_symbol_month"])
    if low > high:
        low, high = high, low

    return {
        "phase": 190,
        "audit_as_of": ev["audit_as_of"],
        "status": "CONDITIONAL_TOP_PRIORITY_REFERENCE_DATA_CANDIDATE",
        "source": ev["source"],
        "history_start": history["start_date"],
        "pit_time_axes": {
            "record_time": "ts_record",
            "effective_time": "ts_effective",
            "database_created_time": "ts_created",
            "first_customer_receipt_verified": pit["first_customer_receipt_timestamp_provided"],
        },
        "unresolved_documentation_conflicts": {
            "instrument_count_scope": not history["instrument_count_scope_reconciled"],
            "update_frequency": cadence_gate,
            "per_symbol_pricing": not pricing["pricing_reconciled"],
        },
        "cost_scenarios": [
            _cost_scenario(n, included, low, high) for n in (1000, 5000, 10000)
        ],
        "admission": {
            "broad_universe_admitted": ev["research_gates"]["broad_universe_admitted"],
            "ftd_identity_crosswalk_admitted": ev["research_gates"]["ftd_identity_crosswalk_admitted"],
            "alpha_test_authorized": ev["research_gates"]["alpha_test_authorized"],
            "return_series_included": ev["research_gates"]["return_series_and_delisting_returns"] == "PASS",
        },
        "controls": controls,
        "decision": (
            "Retain as the highest-priority conditional PIT reference-data candidate. "
            "Do not admit it to the universe, FTD crosswalk, or alpha research until "
            "sample, US-equity coverage, record-time, receipt-time, entitlement, and license gates pass."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("phase190_output/phase190_databento_security_master_audit.json"),
    )
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase": result["phase"],
        "status": result["status"],
        "history_start": result["history_start"],
        "record_time_axis": result["pit_time_axes"]["record_time"],
        "effective_time_axis": result["pit_time_axes"]["effective_time"],
        "pricing_conflict": result["unresolved_documentation_conflicts"]["per_symbol_pricing"],
        "broad_universe_admitted": result["admission"]["broad_universe_admitted"],
        "alpha_test_authorized": result["admission"]["alpha_test_authorized"],
        "f80_frozen": result["controls"]["f80_frozen"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
