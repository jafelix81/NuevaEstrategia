#!/usr/bin/env python3
"""Phase 209: exact-first Form 144/Form 4 linkage sensitivity; no alpha testing."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from research.phase208_form144_form4_execution_conversion_audit import (
    form144_data, form4_blocks, match, sha, family,
)


def candidate_edges(tranches, blocks, min_gap, max_gap):
    index = defaultdict(list)
    for block in blocks:
        index[(block["issuer"], block["owner"])].append(block)
    edges = []
    for tranche in tranches:
        for block in index.get((tranche["issuer"], tranche["seller"]), []):
            gap = (block["date"] - tranche["date"]).days
            if min_gap <= gap <= max_gap:
                edges.append((tranche, block, gap))
    return edges


def mutually_unique(edges):
    td = Counter((t["accession"], t["idx"]) for t, _, _ in edges)
    bd = Counter((b["accession"], b["date"]) for _, b, _ in edges)
    return [e for e in edges
            if td[(e[0]["accession"], e[0]["idx"])] == 1
            and bd[(e[1]["accession"], e[1]["date"])] == 1]


def exact_first_match(tranches, blocks, min_gap=0, max_gap=2):
    exact_edges = [e for e in candidate_edges(tranches, blocks, 0, 0)
                   if e[0]["units"] == e[1]["shares"]]
    td = Counter((t["accession"], t["idx"]) for t, _, _ in exact_edges)
    bd = Counter((b["accession"], b["date"]) for _, b, _ in exact_edges)
    exact_unique = [e for e in exact_edges
                    if td[(e[0]["accession"], e[0]["idx"])] == 1
                    and bd[(e[1]["accession"], e[1]["date"])] == 1]

    # Reserve every node in the exact graph. Ambiguous exact components are
    # quarantined rather than re-matched through weaker date-only candidates.
    reserved_t = {(t["accession"], t["idx"]) for t, _, _ in exact_edges}
    reserved_b = {(b["accession"], b["date"]) for _, b, _ in exact_edges}
    remaining_t = [t for t in tranches if (t["accession"], t["idx"]) not in reserved_t]
    remaining_b = [b for b in blocks if (b["accession"], b["date"]) not in reserved_b]
    fallback_edges = candidate_edges(remaining_t, remaining_b, min_gap, max_gap)
    fallback_unique = mutually_unique(fallback_edges)
    return {
        "exact_edges": exact_edges,
        "exact_unique": exact_unique,
        "exact_ambiguous_tranches": sum(v > 1 for v in td.values()),
        "exact_ambiguous_blocks": sum(v > 1 for v in bd.values()),
        "fallback_edges": fallback_edges,
        "fallback_unique": fallback_unique,
    }


def audit(form144_path, form4_path):
    h144, h4 = sha(form144_path), sha(form4_path)
    rows, originals, eligible, tranches, _ = form144_data(form144_path)
    submissions, rawtx, filing_dates, blocks, _ = form4_blocks(form4_path)
    if h144 != "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659":
        raise ValueError("Unexpected immutable Form 144 input")
    if h4 != "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3":
        raise ValueError("Unexpected immutable Form 4 input")

    broad_candidates, broad_unique = match(tranches, blocks, 0, 2)
    pre_candidates, pre_unique = match(tranches, blocks, -2, -1)
    broad_exact = [x for x in broad_unique if x["diff"] == 0 and x["exact_qty"]]

    exact = exact_first_match(tranches, blocks)
    exact_edges = exact["exact_edges"]
    exact_unique = exact["exact_unique"]
    fallback = exact["fallback_unique"]
    exact_class_agree = [
        e for e in exact_unique
        if e[0]["class_family"] != "UNKNOWN"
        and e[1]["class_family"] != "MULTI_OR_UNKNOWN"
        and e[0]["class_family"] == e[1]["class_family"]
    ]

    broad_edges = candidate_edges(tranches, blocks, 0, 2)
    broad_td = Counter((t["accession"], t["idx"]) for t, _, _ in broad_edges)
    broad_bd = Counter((b["accession"], b["date"]) for _, b, _ in broad_edges)
    collision = Counter()
    for t, b, _ in exact_edges:
        collision[
            ("tranche_collision" if broad_td[(t["accession"], t["idx"])] > 1 else "tranche_unique")
            + "|"
            + ("form4_collision" if broad_bd[(b["accession"], b["date"])] > 1 else "form4_unique")
        ] += 1

    sensitivity = []
    for lo, hi, label in [
        (0, 0, "same_day"), (0, 1, "0_1d"), (0, 2, "0_2d"),
        (0, 3, "0_3d"), (0, 4, "0_4d"), (-1, -1, "minus_1d"),
        (-2, -1, "minus_2_1d"),
    ]:
        edges = candidate_edges(tranches, blocks, lo, hi)
        unique = mutually_unique(edges)
        sensitivity.append({
            "window": label,
            "candidate_pairs": len(edges),
            "mutually_unique_pairs": len(unique),
            "exact_date_and_share_pairs": sum(
                gap == 0 and t["units"] == b["shares"] for t, b, gap in unique
            ),
        })

    total_notice_ids = {
        t["accession"] for t, _, _ in exact_unique
    } | {
        t["accession"] for t, _, _ in fallback
    }
    notice_count = len(eligible)
    return {
        "phase": 209,
        "inputs": {
            "form144_sha256": h144,
            "form144_artifact_run_id": 41959603351,
            "form144_artifact_id": 13385365595,
            "form4_sha256": h4,
            "form4_artifact_run_id": 40606706518,
            "form4_artifact_id": 12781850078,
        },
        "sample": {
            "form144_panel_rows": len(rows),
            "form144_q3_original_notices": len(originals),
            "eligible_notices": notice_count,
            "eligible_tranches": len(tranches),
            "form4_submissions": len(submissions),
            "form4_nonderivative_rows": len(rawtx),
            "form4_unique_owner_sale_blocks": len(blocks),
        },
        "phase208_broad_window_baseline": {
            "window_days": [0, 2],
            "candidate_pairs": len(broad_candidates),
            "mutually_unique_pairs": len(broad_unique),
            "exact_date_and_share_pairs_after_broad_uniqueness": len(broad_exact),
            "pre_notice_candidate_pairs": len(pre_candidates),
            "pre_notice_mutually_unique_pairs": len(pre_unique),
        },
        "exact_edge_graph": {
            "edges": len(exact_edges),
            "distinct_tranches": len({(t["accession"], t["idx"]) for t, _, _ in exact_edges}),
            "distinct_form4_blocks": len({(b["accession"], b["date"]) for _, b, _ in exact_edges}),
            "ambiguous_tranches": exact["exact_ambiguous_tranches"],
            "ambiguous_form4_blocks": exact["exact_ambiguous_blocks"],
            "mutually_unique_edges": len(exact_unique),
            "class_family_agree": len(exact_class_agree),
            "class_family_conflict_or_unresolved": len(exact_unique) - len(exact_class_agree),
            "class_family_agreement_rate": round(len(exact_class_agree) / len(exact_unique), 6),
        },
        "broad_window_collision_diagnostic": {
            "exact_edges_removed_by_phase208_broad_uniqueness": len(exact_edges) - len(broad_exact),
            "collision_patterns": {k: v for k, v in sorted(collision.items())},
        },
        "exact_first_hierarchical_linkage": {
            "exact_date_and_share_matches": len(exact_unique),
            "fallback_candidate_pairs_after_reserving_exact_nodes": len(exact["fallback_edges"]),
            "additional_mutually_unique_fallback_matches": len(fallback),
            "fallback_gap_counts": dict(Counter(str(gap) for _, _, gap in fallback)),
            "total_one_to_one_links": len(exact_unique) + len(fallback),
            "distinct_notices_linked": len(total_notice_ids),
            "rate_of_eligible_notices": round(len(total_notice_ids) / notice_count, 6),
            "exact_date_and_share_rate_of_eligible_notices": round(
                len({t["accession"] for t, _, _ in exact_unique}) / notice_count, 6
            ),
        },
        "window_sensitivity": sensitivity,
        "decision": {
            "phase208_matching_order_requires_correction": True,
            "exact_first_linkage": "PROVISIONAL_DESCRIPTIVE_LINKAGE_ONLY",
            "strict_pit_admitted": False,
            "feature_admitted": False,
            "alpha_test_authorized": False,
            "return_test_run": False,
            "holdout_used": False,
            "legacy_holdout": "CONSUMED_NOT_PRISTINE",
            "f80_frozen": True,
            "production_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144-csv", required=True)
    parser.add_argument("--form4-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.form144_csv, args.form4_zip)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
