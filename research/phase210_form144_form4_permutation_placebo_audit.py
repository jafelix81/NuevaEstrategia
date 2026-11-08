#!/usr/bin/env python3
"""Phase 210: conditional permutation placebos for Form 144/Form 4 linkage."""
import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from research.phase208_form144_form4_execution_conversion_audit import form144_data, form4_blocks, sha
from research.phase209_form144_form4_exact_first_matching_audit import exact_first_match

EXPECTED_FORM144_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
EXPECTED_FORM4_SHA = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"


def quantile_linear(values, q):
    xs = sorted(values)
    if not xs:
        return None
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def statistics_median(values):
    xs = sorted(values)
    n = len(xs)
    if n % 2:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2


def count_unique_mutable_matches(tranches, blocks, owners, dates, shares, mutable_block_ids):
    index = defaultdict(list)
    for bi, block in enumerate(blocks):
        index[(block["issuer"], owners[bi], dates[bi], shares[bi])].append(bi)
    edges = []
    for ti, tranche in enumerate(tranches):
        key = (tranche["issuer"], tranche["seller"], tranche["date"], tranche["units"])
        for bi in index.get(key, []):
            edges.append((ti, bi))
    td = Counter(ti for ti, _ in edges)
    bd = Counter(bi for _, bi in edges)
    return sum(1 for ti, bi in edges if td[ti] == 1 and bd[bi] == 1 and bi in mutable_block_ids)


def permutation_summary(counts, observed, mutable_blocks):
    ge = sum(value >= observed for value in counts)
    mean = sum(counts) / len(counts)
    return {
        "observed_mutable_exact_links": observed,
        "mutable_form4_blocks": mutable_blocks,
        "null_mean": round(mean, 6),
        "null_median": statistics_median(counts),
        "null_p95": round(quantile_linear(counts, 0.95), 6),
        "null_max": max(counts),
        "null_replicates_at_or_above_observed": ge,
        "empirical_tail_plus_one": round((1 + ge) / (len(counts) + 1), 6),
        "observed_to_null_mean_ratio": round(observed / mean, 6) if mean else None,
    }


def run_permutations(tranches, blocks, reps=500, seed=210):
    base_owners = [b["owner"] for b in blocks]
    base_dates = [b["date"] for b in blocks]
    base_shares = [b["shares"] for b in blocks]
    by_issuer, by_owner = defaultdict(list), defaultdict(list)
    for i, block in enumerate(blocks):
        by_issuer[block["issuer"]].append(i)
        by_owner[(block["issuer"], block["owner"])].append(i)

    owner_mutable = {i for ids in by_issuer.values()
                     if len({base_owners[i] for i in ids}) > 1 for i in ids}
    date_mutable = {i for ids in by_owner.values() if len(ids) > 1 for i in ids}

    exact = exact_first_match(tranches, blocks)
    block_index = {(b["accession"], b["date"]): i for i, b in enumerate(blocks)}
    exact_unique = exact["exact_unique"]
    observed_owner = sum(1 for _, b, _ in exact_unique
                         if block_index[(b["accession"], b["date"])] in owner_mutable)
    observed_date = sum(1 for _, b, _ in exact_unique
                        if block_index[(b["accession"], b["date"])] in date_mutable)

    specs = [
        ("owner_identity_within_issuer", "owner", owner_mutable, observed_owner, 0),
        ("date_within_issuer_owner", "date", date_mutable, observed_date, 1),
        ("shares_within_issuer_owner", "shares", date_mutable, observed_date, 2),
        ("date_and_shares_within_issuer_owner", "both", date_mutable, observed_date, 3),
    ]
    summaries = {}
    for label, mode, mutable, observed, offset in specs:
        rng = random.Random(seed + offset)
        counts = []
        for _ in range(reps):
            owners, dates, shares = base_owners.copy(), base_dates.copy(), base_shares.copy()
            if mode == "owner":
                for ids in by_issuer.values():
                    if len({base_owners[i] for i in ids}) > 1:
                        vals = [base_owners[i] for i in ids]
                        rng.shuffle(vals)
                        for i, value in zip(ids, vals):
                            owners[i] = value
            else:
                for ids in by_owner.values():
                    if len(ids) <= 1:
                        continue
                    if mode in ("date", "both"):
                        vals = [base_dates[i] for i in ids]
                        rng.shuffle(vals)
                        for i, value in zip(ids, vals):
                            dates[i] = value
                    if mode in ("shares", "both"):
                        vals = [base_shares[i] for i in ids]
                        rng.shuffle(vals)
                        for i, value in zip(ids, vals):
                            shares[i] = value
            counts.append(count_unique_mutable_matches(tranches, blocks, owners, dates, shares, mutable))
        summaries[label] = permutation_summary(counts, observed, len(mutable))

    return {
        "replicates": reps,
        "seed": seed,
        "group_structure": {
            "issuer_groups": len(by_issuer),
            "issuers_with_multiple_reporting_owners": sum(
                1 for ids in by_issuer.values() if len({base_owners[i] for i in ids}) > 1
            ),
            "issuer_owner_groups": len(by_owner),
            "issuer_owner_groups_with_multiple_form4_blocks": sum(1 for ids in by_owner.values() if len(ids) > 1),
            "owner_identity_mutable_form4_blocks": len(owner_mutable),
            "date_and_share_mutable_form4_blocks": len(date_mutable),
            "exact_links_in_owner_mutable_groups": observed_owner,
            "exact_links_in_date_share_mutable_groups": observed_date,
        },
        "placebos": summaries,
    }


def audit(form144_path, form4_path, reps=500, seed=210):
    form144_sha, form4_sha = sha(form144_path), sha(form4_path)
    if form144_sha != EXPECTED_FORM144_SHA:
        raise ValueError("Unexpected immutable Form 144 input")
    if form4_sha != EXPECTED_FORM4_SHA:
        raise ValueError("Unexpected immutable Form 4 input")
    rows, originals, eligible, tranches, _ = form144_data(form144_path)
    submissions, rawtx, filing_dates, blocks, _ = form4_blocks(form4_path)
    linkage = exact_first_match(tranches, blocks)
    exact_unique = linkage["exact_unique"]
    if len(exact_unique) != 521:
        raise ValueError("Unexpected exact-link graph size")

    family_agree = normalized_equal = 0
    family_pairs = Counter()
    for tranche, block, _ in exact_unique:
        tf, bf = tranche.get("class_family", "UNKNOWN"), block.get("class_family", "MULTI_OR_UNKNOWN")
        family_pairs[f"{tf}|{bf}"] += 1
        if tf == bf and tf not in ("UNKNOWN", "MULTI_OR_UNKNOWN"):
            family_agree += 1
        tn, bn = tranche.get("class_norm", ""), block.get("class_norm", "")
        if tn and bn and tn == bn:
            normalized_equal += 1

    return {
        "phase": 210,
        "inputs": {
            "form144_csv_sha256": form144_sha, "form144_artifact_run_id": 41959603351,
            "form144_artifact_id": 13385365595, "form4_inner_zip_sha256": form4_sha,
            "form4_artifact_run_id": 40606706518, "form4_artifact_id": 12781850078,
        },
        "sample": {
            "form144_panel_rows": len(rows), "eligible_notices": len(eligible),
            "eligible_tranches": len(tranches), "form4_submissions": len(submissions),
            "form4_nonderivative_rows": len(rawtx), "form4_unique_owner_sale_blocks": len(blocks),
        },
        "exact_link_graph": {
            "edges": len(linkage["exact_edges"]), "mutually_unique_edges": len(exact_unique),
            "ambiguous_tranches": linkage["exact_ambiguous_tranches"],
            "ambiguous_form4_blocks": linkage["exact_ambiguous_blocks"],
            "class_family_agree": family_agree,
            "class_family_agreement_rate": round(family_agree / len(exact_unique), 6),
            "normalized_class_text_equal": normalized_equal,
            "family_agree_but_normalized_text_differs": family_agree - normalized_equal,
            "family_conflict_or_unknown": len(exact_unique) - family_agree,
            "class_family_pairs": dict(sorted(family_pairs.items())),
            "fallback_mutually_unique_links": len(linkage["fallback_unique"]),
            "total_hierarchical_links": len(exact_unique) + len(linkage["fallback_unique"]),
        },
        "permutation_audit": run_permutations(tranches, blocks, reps, seed),
        "decision": {
            "disposition": "LINKAGE_PLACEBO_ALIGNMENT_ENHANCED_DESCRIPTIVE_ONLY",
            "strict_pit_admitted": False, "feature_admitted": False,
            "alpha_test_authorized": False, "return_test_run": False,
            "holdout_used": False, "legacy_holdout": "CONSUMED_NOT_PRISTINE",
            "f80_frozen": True, "production_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144-csv", required=True)
    parser.add_argument("--form4-zip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--permutations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=210)
    args = parser.parse_args()
    if args.permutations < 100:
        raise ValueError("Use at least 100 permutations")
    result = audit(args.form144_csv, args.form4_zip, args.permutations, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
