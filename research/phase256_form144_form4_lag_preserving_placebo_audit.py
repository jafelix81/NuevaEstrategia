#!/usr/bin/env python3
"""Phase 256: revalidate Form 144/Form 4 linkage placebos while preserving Form 4 filing lag.

This is a document-linkage diagnostic only. It is not a return-alpha test.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

from research.phase208_form144_form4_execution_conversion_audit import (
    form144_data,
    form4_blocks,
    sha,
)
from research.phase209_form144_form4_exact_first_matching_audit import exact_first_match

EXPECTED_FORM144_SHA = "7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659"
EXPECTED_FORM4_SHA = "a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3"


def build_groups(blocks):
    by_issuer = defaultdict(list)
    by_issuer_owner = defaultdict(list)
    for i, block in enumerate(blocks):
        by_issuer[block["issuer"]].append(i)
        by_issuer_owner[(block["issuer"], block["owner"])].append(i)
    owner_mutable = {
        i
        for ids in by_issuer.values()
        if len({blocks[i]["owner"] for i in ids}) > 1
        for i in ids
    }
    lag_mutable = {i for ids in by_issuer_owner.values() if len(ids) > 1 for i in ids}
    return by_issuer, by_issuer_owner, owner_mutable, lag_mutable


def permute_lags_within_owner_groups(blocks, groups, rng):
    """Permute filing lags within issuer-owner groups, keeping filing dates fixed."""
    by_issuer_owner = groups[1]
    if any(not isinstance(block["lag"], int) or block["lag"] < 0 or block["lag"] > 4 for block in blocks):
        raise ValueError("Form 4 lag outside the admitted 0–4 day sample envelope")
    dates = [block["date"] for block in blocks]
    lags_out = [block["lag"] for block in blocks]
    for ids in by_issuer_owner.values():
        if len(ids) <= 1:
            continue
        lag_values = [blocks[i]["lag"] for i in ids]
        rng.shuffle(lag_values)
        for i, lag in zip(ids, lag_values):
            lags_out[i] = lag
            dates[i] = blocks[i]["filing"] - timedelta(days=lag)
    return dates, lags_out


def count_unique_mutable_matches_fast(tranches, blocks, owners, dates, shares, mutable_block_ids):
    """Count exact one-to-one matches without materializing the full edge list."""
    block_counts = Counter(
        (block["issuer"], owners[i], dates[i], shares[i])
        for i, block in enumerate(blocks)
    )
    unique_block_index = {
        (block["issuer"], owners[i], dates[i], shares[i]): i
        for i, block in enumerate(blocks)
        if block_counts[(block["issuer"], owners[i], dates[i], shares[i])] == 1
    }
    tranche_match_degrees = Counter()
    tranche_keys = []
    for tranche in tranches:
        tranche_id = (tranche["accession"], tranche["idx"])
        key = (tranche["issuer"], tranche["seller"], tranche["date"], tranche["units"])
        tranche_keys.append((tranche_id, key))
        tranche_match_degrees[tranche_id] += block_counts.get(key, 0)
    total = 0
    for tranche_id, key in tranche_keys:
        if tranche_match_degrees[tranche_id] != 1 or block_counts.get(key, 0) != 1:
            continue
        block_index = unique_block_index.get(key)
        if block_index in mutable_block_ids:
            total += 1
    return total


def count_unique_mutable_matches_slow(tranches, blocks, owners, dates, shares, mutable_block_ids):
    """Reference implementation retained for small synthetic regression tests."""
    index = defaultdict(list)
    for bi, block in enumerate(blocks):
        index[(block["issuer"], owners[bi], dates[bi], shares[bi])].append(bi)
    edges = []
    for tranche in tranches:
        tkey = (tranche["accession"], tranche["idx"])
        key = (tranche["issuer"], tranche["seller"], tranche["date"], tranche["units"])
        for bi in index.get(key, []):
            edges.append((tkey, bi))
    td = Counter(tkey for tkey, _ in edges)
    bd = Counter(bi for _, bi in edges)
    return sum(
        1 for tkey, bi in edges
        if td[tkey] == 1 and bd[bi] == 1 and bi in mutable_block_ids
    )


def summarize_counts(counts, observed, mutable_blocks):
    ordered = sorted(counts)
    exceedances = sum(value >= observed for value in ordered)
    n = len(ordered)
    upper = (1.0 - 0.05 ** (1.0 / n)) if exceedances == 0 and n else None
    return {
        "observed_mutable_exact_links": observed,
        "mutable_form4_blocks": mutable_blocks,
        "replicates": n,
        "null_mean": round(sum(ordered) / n, 6),
        "null_median": ordered[n // 2],
        "null_p95": ordered[min(n - 1, int(__import__("math").ceil(0.95 * n) - 1))],
        "null_max": ordered[-1],
        "null_replicates_at_or_above_observed": exceedances,
        "empirical_tail_plus_one": (1 + exceedances) / (n + 1),
        "zero_exceedance_one_sided_95pct_upper": upper,
    }


def measure_raw_date_shuffle_invalidity(blocks, reps=1000, seed=211):
    """Quantify how often Phase 210's raw-date shuffle exits its original lag filter."""
    by_issuer_owner = build_groups(blocks)[1]
    base_dates = [block["date"] for block in blocks]
    rng = random.Random(seed)
    invalid_counts = []
    negative_counts = []
    over_four_counts = []
    for _ in range(reps):
        dates = base_dates.copy()
        for ids in by_issuer_owner.values():
            if len(ids) <= 1:
                continue
            values = [base_dates[i] for i in ids]
            rng.shuffle(values)
            for i, value in zip(ids, values):
                dates[i] = value
        negative = sum(1 for i, block in enumerate(blocks) if (block["filing"] - dates[i]).days < 0)
        over_four = sum(1 for i, block in enumerate(blocks) if (block["filing"] - dates[i]).days > 4)
        negative_counts.append(negative)
        over_four_counts.append(over_four)
        invalid_counts.append(negative + over_four)
    ordered = sorted(invalid_counts)
    return {
        "replicates": reps,
        "blocks_per_replicate": len(blocks),
        "mean_invalid_blocks": round(sum(invalid_counts) / reps, 6),
        "median_invalid_blocks": ordered[reps // 2],
        "p95_invalid_blocks": ordered[min(reps - 1, int(__import__("math").ceil(0.95 * reps) - 1))],
        "max_invalid_blocks": ordered[-1],
        "mean_negative_lag_blocks": round(sum(negative_counts) / reps, 6),
        "mean_lag_over_4_blocks": round(sum(over_four_counts) / reps, 6),
        "mean_invalid_fraction": round(sum(invalid_counts) / (reps * len(blocks)), 8),
    }


def run_permutations(tranches, blocks, exact_unique, reps=1000, seed=210):
    if reps < 100:
        raise ValueError("Use at least 100 permutations")
    base_owners = [block["owner"] for block in blocks]
    base_dates = [block["date"] for block in blocks]
    base_shares = [block["shares"] for block in blocks]
    base_lags = [block["lag"] for block in blocks]
    if any(not isinstance(lag, int) or lag < 0 or lag > 4 for lag in base_lags):
        raise ValueError("Observed Form 4 block outside the 0–4 day eligibility envelope")
    groups = build_groups(blocks)
    by_issuer, by_issuer_owner, owner_mutable, lag_mutable = groups
    block_index = {(block["accession"], block["date"]): i for i, block in enumerate(blocks)}
    observed_owner = sum(
        1 for _, block, _ in exact_unique
        if block_index[(block["accession"], block["date"])] in owner_mutable
    )
    observed_lag = sum(
        1 for _, block, _ in exact_unique
        if block_index[(block["accession"], block["date"])] in lag_mutable
    )
    specs = [
        ("owner_identity_within_issuer", "owner", owner_mutable, observed_owner, 0),
        ("filing_lag_within_issuer_owner", "lag", lag_mutable, observed_lag, 1),
        ("shares_within_issuer_owner", "shares", lag_mutable, observed_lag, 2),
        ("filing_lag_and_shares_within_issuer_owner", "both", lag_mutable, observed_lag, 3),
    ]
    summaries = {}
    for label, mode, mutable, observed, offset in specs:
        rng = random.Random(seed + offset)
        counts = []
        for _ in range(reps):
            owners = base_owners.copy()
            dates = base_dates.copy()
            shares = base_shares.copy()
            if mode == "owner":
                for ids in by_issuer.values():
                    if len({base_owners[i] for i in ids}) > 1:
                        values = [base_owners[i] for i in ids]
                        rng.shuffle(values)
                        for i, value in zip(ids, values):
                            owners[i] = value
            else:
                if mode in ("lag", "both"):
                    dates, permuted_lags = permute_lags_within_owner_groups(blocks, groups, rng)
                    if not all(0 <= lag <= 4 for lag in permuted_lags):
                        raise AssertionError("Permuted Form 4 lag escaped the eligible envelope")
                for ids in by_issuer_owner.values():
                    if len(ids) <= 1:
                        continue
                    if mode in ("shares", "both"):
                        values = [base_shares[i] for i in ids]
                        rng.shuffle(values)
                        for i, value in zip(ids, values):
                            shares[i] = value
            counts.append(count_unique_mutable_matches_fast(
                tranches, blocks, owners, dates, shares, mutable
            ))
        summaries[label] = summarize_counts(counts, observed, len(mutable))
    return {
        "replicates": reps,
        "seed": seed,
        "lag_null_design": "permute filing-to-transaction calendar-day lag within issuer × reporting-owner groups; keep each block's filing date fixed; reconstruct transaction date as filing date minus permuted lag",
        "group_structure": {
            "issuer_groups": len(by_issuer),
            "issuers_with_multiple_reporting_owners": sum(
                1 for ids in by_issuer.values() if len({base_owners[i] for i in ids}) > 1
            ),
            "issuer_owner_groups": len(by_issuer_owner),
            "issuer_owner_groups_with_multiple_form4_blocks": sum(
                1 for ids in by_issuer_owner.values() if len(ids) > 1
            ),
            "owner_identity_mutable_form4_blocks": len(owner_mutable),
            "lag_share_mutable_form4_blocks": len(lag_mutable),
            "exact_links_in_owner_mutable_groups": observed_owner,
            "exact_links_in_lag_share_mutable_groups": observed_lag,
            "original_lag_min": min(base_lags),
            "original_lag_max": max(base_lags),
            "all_original_lags_within_0_4": all(0 <= lag <= 4 for lag in base_lags),
        },
        "placebos": summaries,
    }


def audit(form144_path, form4_path, reps=1000, seed=210):
    form144_sha = sha(form144_path)
    form4_sha = sha(form4_path)
    if form144_sha != EXPECTED_FORM144_SHA:
        raise ValueError("Unexpected immutable Form 144 input")
    if form4_sha != EXPECTED_FORM4_SHA:
        raise ValueError("Unexpected immutable Form 4 input")
    rows, originals, eligible, tranches, _ = form144_data(form144_path)
    submissions, rawtx, filing_dates, blocks, _ = form4_blocks(form4_path)
    if max(filing_dates).isoformat() != "2026-09-30":
        raise ValueError("Unexpected Form 4 snapshot end")
    linkage = exact_first_match(tranches, blocks)
    exact_unique = linkage["exact_unique"]
    fallback_unique = linkage["fallback_unique"]
    if len(exact_unique) != 521 or len(fallback_unique) != 49:
        raise ValueError("Unexpected immutable exact-first linkage graph")
    permutations = run_permutations(tranches, blocks, exact_unique, reps, seed)
    raw_date_invalidity = measure_raw_date_shuffle_invalidity(blocks, reps, seed + 1)
    return {
        "phase": 256,
        "status": "FORM144_FORM4_LINKAGE_PLACEBOS_REVALIDATED_WITH_FILING_LAG_PRESERVED;_DESCRIPTIVE_ONLY",
        "inputs": {
            "form144_csv_sha256": form144_sha,
            "form144_artifact_run_id": 41959603351,
            "form144_artifact_id": 13385365595,
            "form4_inner_zip_sha256": form4_sha,
            "form4_artifact_run_id": 40606706518,
            "form4_artifact_id": 12781850078,
        },
        "sample": {
            "form144_panel_rows": len(rows),
            "eligible_notices": len(eligible),
            "eligible_tranches": len(tranches),
            "form4_submissions": len(submissions),
            "form4_nonderivative_rows": len(rawtx),
            "form4_unique_owner_sale_blocks": len(blocks),
            "exact_date_share_links": len(exact_unique),
            "fallback_links": len(fallback_unique),
        },
        "permutation_audit": permutations,
        "phase210_raw_date_shuffle_invalidity": raw_date_invalidity,
        "interpretation": {
            "date_placebo_correction": "Phase 210 shuffled raw transaction dates while holding filing dates fixed. Phase 256 permutes the observed 0–4 calendar-day filing lag within issuer-owner groups and reconstructs transaction dates, preserving sample eligibility.",
            "linkage_only": True,
            "form4_code_s_may_include_private_dispositions": True,
            "form144_is_proposed_not_executed": True,
            "not_a_return_or_alpha_p_value": True,
        },
        "decision": {
            "strict_pit_admitted": False,
            "feature_admitted": False,
            "alpha_test_authorized": False,
            "return_test_run": False,
            "bootstrap_loo_oos_run": False,
            "holdout_used": False,
            "legacy_holdout": "CONSUMED_NOT_PRISTINE",
            "f80_frozen": True,
            "production_changed": False,
            "universe_changed": False,
            "capital_changed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--form144-csv", required=True)
    parser.add_argument("--form4-zip", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=210)
    args = parser.parse_args()
    result = audit(args.form144_csv, args.form4_zip, args.permutations, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
