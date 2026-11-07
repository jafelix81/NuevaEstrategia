#!/usr/bin/env python3
"""Phase 192: curated SEC XML-snippet discovery gate for N-PORT direct shorts.

This is an evidence-ledger validator only. It does not download or parse raw
SEC XML, estimate prevalence, reconstruct a PIT panel, or test returns.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

EVIDENCE_PATH = Path(__file__).with_name("phase192_nport_direct_short_equity_sample_discovery.json")
REQUIRED_FIELDS = ("filing_year", "accession", "registrant_cik", "payoff_profile",
                   "asset_category", "issuer_category", "investment_country", "source_url")


def load_evidence(path: Path = EVIDENCE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    ev = evidence if evidence is not None else load_evidence()
    if ev.get("phase") != 192:
        raise ValueError("Unexpected Phase 192 evidence identity")
    rows, partial = ev["complete_short_rows"], ev["partial_filing_discoveries"]
    controls, gates = ev["controls"], ev["admission_gates"]
    if len(rows) < 8 or len({r["filing_year"] for r in rows}) < 4:
        raise ValueError("Purposive sample must have at least eight complete excerpts across four years")
    for row in rows:
        missing = [k for k in REQUIRED_FIELDS if k not in row]
        if missing:
            raise ValueError(f"Sample row missing required fields: {missing}")
        if row["payoff_profile"].lower() != "short":
            raise ValueError("Non-short row entered the direct-short discovery ledger")
        if (row["asset_category"], row["issuer_category"], row["investment_country"]) != ("EC", "CORP", "US"):
            raise ValueError("Row does not meet the narrow non-derivative US corporate common-equity filter")
        if not row["source_url"].startswith("https://www.sec.gov/Archives/edgar/data/"):
            raise ValueError("Only SEC-hosted primary documents are admissible discovery sources")
        if row.get("units") == "NS" and (not isinstance(row.get("balance"), (int, float)) or row["balance"] >= 0):
            raise ValueError("Observed NS short balance must be negative")
        if row.get("currency_value_usd", 0) >= 0 or row.get("pct_net_assets", 0) >= 0:
            raise ValueError("Observed direct-short USD value and NAV percentage must be negative")
    if controls["raw_xml_files_downloaded"] or controls["raw_xml_sha256_verified"]:
        raise ValueError("Do not claim raw XML retrieval or hashing")
    if controls["representative_random_sample"] or controls["prevalence_estimated"]:
        raise ValueError("Purposive search discovery cannot be representative or estimate prevalence")
    for key in ("return_test_run", "alpha_test_run", "bootstrap_or_loo_run", "holdout_used",
                "production_changed", "data_purchase", "vendor_contact"):
        if controls[key]:
            raise ValueError(f"Phase 192 must keep control false: {key}")
    if not controls["f80_frozen"] or controls["phase27o_long_accumulation_results_reused"]:
        raise ValueError("Frozen baseline and Phase 27O separation must be preserved")
    if gates["indexed_xml_short_row_discovery"] != "PASS_PURPOSIVE_SAMPLE" or gates["alpha_test"] != "NOT_AUTHORIZED":
        raise ValueError("Unexpected admission decision")
    if any(t["timezone_and_acceptance_semantics_verified"] for t in ev["timestamp_observations"]):
        raise ValueError("Directory timestamp observations must not be promoted to acceptance times")
    return {
        "phase": 192, "audit_as_of": ev["audit_as_of"], "status": ev["status"],
        "classification": ev["classification"], "discovery_method": ev["discovery_method"],
        "complete_short_row_excerpts": len(rows),
        "complete_sample_filing_years": sorted({r["filing_year"] for r in rows}),
        "distinct_complete_accessions": len({r["accession"] for r in rows}),
        "partial_filing_discoveries": len(partial),
        "raw_xml_sha256_verified": controls["raw_xml_sha256_verified"],
        "prevalence_estimated": controls["prevalence_estimated"],
        "broad_pit_universe_admitted": gates["broad_pit_universe"],
        "alpha_test_authorized": gates["alpha_test"] == "PASS",
        "f80_frozen": controls["f80_frozen"], "decision": ev["decision"]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase192_output/phase192_nport_short_discovery_audit.json"))
    args = parser.parse_args()
    result = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
