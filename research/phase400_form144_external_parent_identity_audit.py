#!/usr/bin/env python3
"""Offline audit of the three externally recovered Form 144/A parent documents."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def audit(payload: dict) -> dict:
    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 3:
        raise ValueError("Phase 400 expects exactly three recovered external parent-child pairs")

    seen_parents = set()
    seen_amendments = set()
    issuer_changes = 0
    filer_stable = 0
    units_same = 0
    value_same = 0
    outstanding_changed = 0
    rows = []

    for pair in pairs:
        parent = pair["parent"]
        amendment = pair["amendment"]
        parent_accession = parent["accession"]
        amendment_accession = amendment["accession"]

        if parent_accession in seen_parents or amendment_accession in seen_amendments:
            raise ValueError("duplicate accession in Phase 400 pair set")
        seen_parents.add(parent_accession)
        seen_amendments.add(amendment_accession)

        linked = amendment.get("previous_accession") == parent_accession
        if not linked:
            raise ValueError(f"amendment does not explicitly link to parent: {amendment_accession}")

        issuer_changed = parent["issuer_cik"] != amendment["issuer_cik"]
        if issuer_changed:
            issuer_changes += 1
        same_filer = parent["filer_cik"] == amendment["filer_cik"]
        if same_filer:
            filer_stable += 1

        same_units = parent["units_to_be_sold"] == amendment["units_to_be_sold"]
        if same_units:
            units_same += 1
        same_value = parent["aggregate_market_value_usd"] == amendment["aggregate_market_value_usd"]
        if same_value:
            value_same += 1
        if parent["units_outstanding_raw"] != amendment["units_outstanding_raw"]:
            outstanding_changed += 1

        rows.append({
            "ticker": pair["ticker"],
            "parent_accession": parent_accession,
            "amendment_accession": amendment_accession,
            "parent_census_status": pair["parent_census_status"],
            "previous_accession_link_valid": linked,
            "issuer_cik_changed": issuer_changed,
            "filer_cik_stable": same_filer,
            "sale_units_unchanged": same_units,
            "aggregate_market_value_unchanged": same_value,
            "outstanding_raw_changed": parent["units_outstanding_raw"] != amendment["units_outstanding_raw"],
            "corrected_issuer_identity_first_known": amendment["filing_date"],
            "issuer_attribution_before_amendment_allowed": False,
        })

    if issuer_changes != 3 or filer_stable != 3 or units_same != 3 or value_same != 3:
        raise ValueError("observed Phase 400 identity or economic-field controls did not reconcile")

    panel = payload["panel_reconciliation"]
    return {
        "phase": 400,
        "external_parent_child_pairs": len(rows),
        "explicit_previous_accession_links": sum(r["previous_accession_link_valid"] for r in rows),
        "issuer_cik_changes": issuer_changes,
        "filer_cik_stable_pairs": filer_stable,
        "sale_units_unchanged_pairs": units_same,
        "aggregate_market_value_unchanged_pairs": value_same,
        "outstanding_raw_value_changed_pairs": outstanding_changed,
        "phase67_form_144a_rows": panel["form_144a_rows"],
        "phase67_matched_parent_pairs": panel["parents_matched_in_candidate_issuer_event_panel"],
        "phase67_total_parent_pairs_accounted_for": panel["parents_matched_in_candidate_issuer_event_panel"] + len(rows),
        "phase67_total_issuer_cik_change_pairs": len(rows) + panel["matched_193_parent_child_pairs_with_issuer_cik_change"],
        "phase67_issuer_cik_change_rate": (len(rows) + panel["matched_193_parent_child_pairs_with_issuer_cik_change"]) / panel["form_144a_rows"],
        "matched_pairs_with_issuer_cik_change": panel["matched_193_parent_child_pairs_with_issuer_cik_change"],
        "matched_pairs_with_issuer_name_text_difference": panel["matched_193_pairs_with_issuer_name_text_difference"],
        "external_parent_cases_are_not_a_random_sample": True,
        "event_policy": {
            "amendment_is_new_sale": False,
            "corrected_issuer_identity_may_be_backdated": False,
            "parent_issuer_attribution_before_correction": "BLOCKED_WHEN_PARENT_ISSUER_IDENTITY_CONFLICTS",
            "first_correct_issuer_identity_known_date": "amendment filing date",
            "earliest_research_use": "first regular NYSE session strictly after amendment filing date",
        },
        "no_of_units_outstanding_feature": "KILLED; raw value retained only for version comparison",
        "forward_returns_used": False,
        "economic_test_authorized": False,
        "f80_changed": False,
        "holdout_used": False,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name(
        "PHASE400_FORM144_EXTERNAL_PARENT_IDENTITY_SUMMARY_2026-11-14.json"
    ))
    parser.add_argument("--output", type=Path, default=Path("phase400_summary.json"))
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = audit(payload)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
