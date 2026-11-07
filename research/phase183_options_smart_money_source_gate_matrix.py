"""Phase 183: cross-source Smart Money data-admission matrix.

Evidence-only validator. It does not download data, calculate returns, access a
holdout, contact vendors, or change production.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT_INPUT = Path(__file__).with_name("phase183_options_smart_money_source_gate_matrix.json")


def audit(snapshot: dict) -> dict:
    gate_names = snapshot["gate_names"]
    sources = snapshot["sources"]
    ids = [s["id"] for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source id")
    ranks = [s["priority_rank"] for s in sources]
    if len(ranks) != len(set(ranks)):
        raise ValueError("priority ranks must be unique")
    results = []
    for source in sources:
        gates = source["gates"]
        if set(gates) != set(gate_names):
            raise ValueError(f"gate schema mismatch for {source['id']}")
        passed = [name for name in gate_names if gates[name] is True]
        failed = [name for name in gate_names if gates[name] is not True]
        pit_ready = len(failed) == 0
        if pit_ready:
            raise ValueError("no source may be admitted without a separately reviewed alpha protocol")
        results.append({
            "id": source["id"],
            "name": source["name"],
            "priority_rank": source["priority_rank"],
            "decision": source["decision"],
            "gates_passed": len(passed),
            "gates_total": len(gate_names),
            "failed_gates": failed,
            "pit_admitted": False,
            "alpha_admitted": False
        })
    results.sort(key=lambda x: x["priority_rank"])
    decisions = snapshot["global_decisions"]
    if decisions["alpha_test_authorized"] or decisions["holdout_used"] or decisions["vendor_contact"] or decisions["data_purchase"] or decisions["production_changed"]:
        raise ValueError("phase 183 scope/control violation")
    if not decisions["f80_frozen"]:
        raise ValueError("F80 must remain frozen")
    if decisions["priority_is_expected_alpha_rank"]:
        raise ValueError("priority rank must not be interpreted as expected alpha")
    return {
        "phase": 183,
        "audit_date": snapshot["audit_date"],
        "status": "NO_SOURCE_PIT_ADMITTED_NO_ALPHA_TEST_AUTHORIZED",
        "source_count": len(results),
        "pit_admitted_count": sum(x["pit_admitted"] for x in results),
        "alpha_admitted_count": sum(x["alpha_admitted"] for x in results),
        "ranking_semantics": "research sequencing by evidence readiness and complementary measurement role; not expected alpha",
        "sources": results,
        "controls": {
            "f80_frozen": True,
            "holdout_used": False,
            "vendor_contact": False,
            "data_purchase": False,
            "production_changed": False
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=Path("phase183_output"))
    args = parser.parse_args()
    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    result = audit(snapshot)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "phase183_source_gate_matrix_audit.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
